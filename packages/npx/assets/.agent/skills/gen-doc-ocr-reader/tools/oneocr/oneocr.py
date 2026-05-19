import ctypes
import sys
import os
import copy
from ctypes import Structure, byref, POINTER, c_int64, c_int32, c_float, c_ubyte, c_char, c_char_p
from PIL import Image
from contextlib import contextmanager

CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'oneocr')
MODEL_NAME = 'oneocr.onemodel'
DLL_NAME = 'oneocr.dll'
MODEL_KEY = b"kj)TGtrK>f]b[Piow.gU+nC@s\"\"\"\"\"\"4"

c_int64_p = POINTER(c_int64)
c_float_p = POINTER(c_float)
c_ubyte_p = POINTER(c_ubyte)

class ImageStructure(Structure):
    '''Image data structure'''
    _fields_ = [
        ('type', c_int32),
        ('width', c_int32),      # Image width in pixels
        ('height', c_int32),     # Image height in pixels
        ('_reserved', c_int32),
        ('step_size', c_int64),  # Bytes per row
        ('data_ptr', c_ubyte_p)  # Pointer to image data
    ]

class BoundingBox(Structure):
    '''Text bounding box coordinates'''
    _fields_ = [
        ('x1', c_float),
        ('y1', c_float),
        ('x2', c_float),
        ('y2', c_float),
        ('x3', c_float),
        ('y3', c_float),
        ('x4', c_float),
        ('y4', c_float)
    ]

BoundingBox_p = POINTER(BoundingBox)

DLL_FUNCTIONS = [
    ('CreateOcrInitOptions', [c_int64_p], c_int64),
    ('OcrInitOptionsSetUseModelDelayLoad', [c_int64, c_char], c_int64),
    ('CreateOcrPipeline', [c_char_p, c_char_p, c_int64, c_int64_p], c_int64),
    ('CreateOcrProcessOptions', [c_int64_p], c_int64),
    ('OcrProcessOptionsSetMaxRecognitionLineCount', [c_int64, c_int64], c_int64),
    ('RunOcrPipeline', [c_int64, POINTER(ImageStructure), c_int64, c_int64_p], c_int64),

    ('GetImageAngle', [c_int64, c_float_p], c_int64),
    ('GetOcrLineCount', [c_int64, c_int64_p], c_int64),
    ('GetOcrLine', [c_int64, c_int64, c_int64_p], c_int64),
    ('GetOcrLineContent', [c_int64, POINTER(c_char_p)], c_int64),
    ('GetOcrLineBoundingBox', [c_int64, POINTER(BoundingBox_p)], c_int64),
    ('GetOcrLineWordCount', [c_int64, c_int64_p], c_int64),
    ('GetOcrWord', [c_int64, c_int64, c_int64_p], c_int64),
    ('GetOcrWordContent', [c_int64, POINTER(c_char_p)], c_int64),
    ('GetOcrWordBoundingBox', [c_int64, POINTER(BoundingBox_p)], c_int64),
    ('GetOcrWordConfidence', [c_int64, c_float_p], c_int64),

    ('ReleaseOcrResult', [c_int64], None),
    ('ReleaseOcrInitOptions', [c_int64], None),
    ('ReleaseOcrPipeline', [c_int64], None),
    ('ReleaseOcrProcessOptions', [c_int64], None)
]

@contextmanager
def suppress_output():
    '''Suppress stdout/stderr'''
    devnull = os.open(os.devnull, os.O_WRONLY)
    original_stdout = os.dup(1)
    original_stderr = os.dup(2)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    try:
        yield
    finally:
        os.dup2(original_stdout, 1)
        os.dup2(original_stderr, 2)
        os.close(original_stdout)
        os.close(original_stderr)
        os.close(devnull)

class OcrEngine:    
    def __init__(self):
        self._load_dll()
        self.init_options = self._create_init_options()
        self.pipeline = self._create_pipeline()
        self.process_options = self._create_process_options()
        self.empty_result = {
                'text': '',
                'text_angle': None,
                'lines': []
            }

    def __del__(self):
        if self.ocr_dll:
            self.ocr_dll.ReleaseOcrProcessOptions(self.process_options)
            self.ocr_dll.ReleaseOcrPipeline(self.pipeline)
            self.ocr_dll.ReleaseOcrInitOptions(self.init_options)

    def _bind_dll_functions(self, dll, functions):
        '''Dynamically bind function specifications to DLL methods'''
        for name, argtypes, restype in functions:
            try:
                func = getattr(dll, name)
                func.argtypes = argtypes
                func.restype = restype
            except AttributeError as e:
                raise RuntimeError(f'Missing DLL function: {name}') from e

    def _load_dll(self):
        self.ocr_dll = None
        is_wine = os.environ.get('ONEOCR_WINE_MODE') == '1' or 'WINEPREFIX' in os.environ
        
        try:
            # Load kernel32 for DLL directory configuration
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            if hasattr(kernel32, 'SetDllDirectoryW'):
                kernel32.SetDllDirectoryW(CONFIG_DIR)

            dll_path = os.path.join(CONFIG_DIR, DLL_NAME)
            
            # Verify DLL file exists before attempting to load
            if not os.path.exists(dll_path):
                raise RuntimeError(
                    f'DLL file not found at {dll_path}. '
                    f'Please ensure oneocr.dll, oneocr.onemodel, and onnxruntime.dll '
                    f'are placed in {CONFIG_DIR}'
                )
            
            ocr_dll = ctypes.WinDLL(dll_path)
            self._bind_dll_functions(ocr_dll, DLL_FUNCTIONS)
            self.ocr_dll = ocr_dll
        except (OSError, RuntimeError) as e:
            if is_wine:
                raise RuntimeError(
                    f'DLL initialization failed in Wine environment: {e}\n'
                    f'Make sure Wine is properly configured and Visual C++ Runtime is installed.\n'
                    f'You may need to run: winetricks vcrun2019'
                ) from e
            else:
                raise RuntimeError(f'DLL initialization failed: {e}') from e

    def _create_init_options(self):
        init_options = c_int64()
        self._check_dll_result(
            self.ocr_dll.CreateOcrInitOptions(byref(init_options)),
            'Init options creation failed'
        )
        
        self._check_dll_result(
            self.ocr_dll.OcrInitOptionsSetUseModelDelayLoad(init_options, 0),
            'Model loading config failed'
        )
        return init_options

    def _create_pipeline(self):
        model_path = os.path.join(CONFIG_DIR, MODEL_NAME)
        model_buf = ctypes.create_string_buffer(model_path.encode())
        key_buf = ctypes.create_string_buffer(MODEL_KEY)

        pipeline = c_int64()
        with suppress_output():
            self._check_dll_result(
                self.ocr_dll.CreateOcrPipeline(
                    model_buf,
                    key_buf,
                    self.init_options,
                    byref(pipeline)
                ),
                'Pipeline creation failed'
            )
        return pipeline

    def _create_process_options(self):
        process_options = c_int64()
        self._check_dll_result(
            self.ocr_dll.CreateOcrProcessOptions(byref(process_options)),
            'Process options creation failed'
        )
        
        self._check_dll_result(
            self.ocr_dll.OcrProcessOptionsSetMaxRecognitionLineCount(
                process_options, 1000),
            'Line count config failed'
        )
        return process_options

    def recognize_pil(self, image):
        '''Process PIL Image object'''
        if any(x < 50 or x > 10000 for x in image.size):
            result = copy.deepcopy(self.empty_result)
            result['error'] = 'Unsupported image size'
            return result

        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Convert to BGRA format expected by DLL
        b, g, r, a = image.split()
        bgra_image = Image.merge('RGBA', (b, g, r, a))

        return self._process_image(
            cols=bgra_image.width,
            rows=bgra_image.height,
            step=bgra_image.width * 4,
            data=bgra_image.tobytes()
        )

    def recognize_cv2(self, image_buffer):
        '''Process OpenCV image buffer'''
        import cv2
        import numpy as np

        # If image_buffer is already a numpy array use it directly
        if isinstance(image_buffer, np.ndarray):
            img = image_buffer
        else:
            # Otherwise, try to decode it as a compressed image buffer
            img = cv2.imdecode(image_buffer, cv2.IMREAD_UNCHANGED)
            if img is None:
                result = copy.deepcopy(self.empty_result)
                result['error'] = 'Failed to decode image'
                return result

        if any(x < 50 or x > 10000 for x in img.shape[:2]):
            result = copy.deepcopy(self.empty_result)
            result['error'] = 'Unsupported image size'
            return result

        # Convert to BGRA format expected by DLL
        channels = img.shape[2] if len(img.shape) == 3 else 1
        if channels == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif channels == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

        return self._process_image(
            cols=img.shape[1],
            rows=img.shape[0],
            step=img.shape[1] * 4,
            data=img.ctypes.data
        )

    def _process_image(self, cols, rows, step, data):
        '''Create image structure'''
        if isinstance(data, bytes):
            data_ptr = (c_ubyte * len(data)).from_buffer_copy(data)
        else:
            data_ptr = ctypes.cast(ctypes.c_void_p(data), c_ubyte_p)
        
        img_struct = ImageStructure(
            type=3,
            width=cols,
            height=rows,
            _reserved=0,
            step_size=step,
            data_ptr=data_ptr
        )

        return self._perform_ocr(img_struct)

    def _perform_ocr(self, image_struct):
        '''Execute OCR pipeline and parse results'''
        ocr_result = c_int64()
        if self.ocr_dll.RunOcrPipeline(
                self.pipeline,
                byref(image_struct),
                self.process_options,
                byref(ocr_result)
            ) != 0:
            return self.empty_result

        parsed_result = self._parse_ocr_results(ocr_result)
        self.ocr_dll.ReleaseOcrResult(ocr_result)
        return parsed_result

    def _parse_ocr_results(self, ocr_result):
        '''Extract and format OCR results from DLL'''
        line_count = c_int64()
        if self.ocr_dll.GetOcrLineCount(ocr_result, byref(line_count)) != 0:
            return self.empty_result

        lines = self._get_lines(ocr_result, line_count)
        return {
            'text': '\n'.join(line['text'] for line in lines),
            'text_angle': self._get_text_angle(ocr_result),
            'lines': lines
        }

    def _get_text_angle(self, ocr_result):
        '''Extract text angle'''
        text_angle = c_float()
        if self.ocr_dll.GetImageAngle(ocr_result, byref(text_angle)) != 0:
            return None
        return text_angle.value

    def _get_lines(self, ocr_result, line_count):
        '''Extract individual text lines'''
        return [self._process_line(ocr_result, idx) for idx in range(line_count.value)]

    def _process_line(self, ocr_result, line_index):
        '''Process a single text line'''
        line_handle = c_int64()
        if self.ocr_dll.GetOcrLine(ocr_result, line_index, byref(line_handle)) != 0:
            return {
                'text': None,
                'bounding_rect': None,
                'words': []
            }

        return {
            'text': self._get_text(line_handle, self.ocr_dll.GetOcrLineContent),
            'bounding_rect': self._get_bounding_box(line_handle, self.ocr_dll.GetOcrLineBoundingBox),
            'words': self._get_words(line_handle)
        }

    def _get_words(self, line_handle):
        '''Extract words from a text line'''
        word_count = c_int64()
        if self.ocr_dll.GetOcrLineWordCount(line_handle, byref(word_count)) != 0:
            return []

        return [self._process_word(line_handle, idx) for idx in range(word_count.value)]

    def _process_word(self, line_handle, word_index):
        '''Process individual word'''
        word_handle = c_int64()
        if self.ocr_dll.GetOcrWord(line_handle, word_index, byref(word_handle)) != 0:
            return {
                'text': None,
                'bounding_rect': None,
                'confidence': None
            }

        return {
            'text': self._get_text(word_handle, self.ocr_dll.GetOcrWordContent),
            'bounding_rect': self._get_bounding_box(word_handle, self.ocr_dll.GetOcrWordBoundingBox),
            'confidence': self._get_word_confidence(word_handle)
        }

    def _get_text(self, handle, text_function):
        '''Extract text content from handle'''
        content = c_char_p()
        if text_function(handle, byref(content)) == 0:
            return content.value.decode('utf-8', errors='ignore')
        return None

    def _get_bounding_box(self, handle, bbox_function):
        '''Extract bounding box from handle'''
        bbox_ptr = BoundingBox_p()
        if bbox_function(handle, byref(bbox_ptr)) == 0 and bbox_ptr:
            bbox = bbox_ptr.contents
            return {
                'x1': bbox.x1,
                'y1': bbox.y1,
                'x2': bbox.x2,
                'y2': bbox.y2,
                'x3': bbox.x3,
                'y3': bbox.y3,
                'x4': bbox.x4,
                'y4': bbox.y4
            }
        return None

    def _get_word_confidence(self, word_handle):
        '''Extract confidence value from word handle'''
        confidence = c_float()
        if self.ocr_dll.GetOcrWordConfidence(word_handle, byref(confidence)) == 0:
            return confidence.value
        return None

    def _check_dll_result(self, result_code, error_message):
        if result_code != 0:
            raise RuntimeError(f'{error_message} (Code: {result_code})')

def serve():
    '''Initialize and run the OCR web service'''
    import json
    import uvicorn
    from io import BytesIO
    from typing import Optional, List
    from fastapi import FastAPI, Request, Response, File, UploadFile, Body
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field

    # Pydantic models for API documentation
    class BoundingRect(BaseModel):
        """Bounding box coordinates for text region"""
        x1: float = Field(..., description="Top-left X coordinate")
        y1: float = Field(..., description="Top-left Y coordinate")
        x2: float = Field(..., description="Top-right X coordinate")
        y2: float = Field(..., description="Top-right Y coordinate")
        x3: float = Field(..., description="Bottom-right X coordinate")
        y3: float = Field(..., description="Bottom-right Y coordinate")
        x4: float = Field(..., description="Bottom-left X coordinate")
        y4: float = Field(..., description="Bottom-left Y coordinate")

    class Word(BaseModel):
        """Individual word recognition result"""
        text: Optional[str] = Field(None, description="Recognized word text")
        bounding_rect: Optional[BoundingRect] = Field(None, description="Word bounding box")
        confidence: Optional[float] = Field(None, description="Recognition confidence score (0-1)")

    class Line(BaseModel):
        """Text line recognition result"""
        text: Optional[str] = Field(None, description="Full line text")
        bounding_rect: Optional[BoundingRect] = Field(None, description="Line bounding box")
        words: List[Word] = Field(default_factory=list, description="Words in this line")

    class OCRResult(BaseModel):
        """OCR processing result"""
        text: str = Field(..., description="Full extracted text from image")
        text_angle: Optional[float] = Field(None, description="Text rotation angle in radians")
        lines: List[Line] = Field(default_factory=list, description="Detected text lines")
        error: Optional[str] = Field(None, description="Error message if processing failed")

        class Config:
            schema_extra = {
                "example": {
                    "text": "Sample text from image",
                    "text_angle": 0.064377,
                    "lines": [
                        {
                            "text": "Sample text",
                            "bounding_rect": {
                                "x1": 13.0, "y1": 38.0,
                                "x2": 458.0, "y2": 38.0,
                                "x3": 458.0, "y3": 77.0,
                                "x4": 13.0, "y4": 76.0
                            },
                            "words": [
                                {
                                    "text": "Sample",
                                    "bounding_rect": {
                                        "x1": 14.35, "y1": 39.69,
                                        "x2": 140.34, "y2": 41.31,
                                        "x3": 139.93, "y3": 73.41,
                                        "x4": 13.77, "y4": 74.08
                                    },
                                    "confidence": 0.987
                                }
                            ]
                        }
                    ]
                }
            }

    # FastAPI app with OpenAPI metadata
    app = FastAPI(
        title="OneOCR API",
        description="""
# OneOCR - Text Recognition API

OneOCR cung cấp API để nhận diện văn bản từ hình ảnh sử dụng Windows 11 Snipping Tool OCR.

OneOCR provides an API for text recognition from images using Windows 11 Snipping Tool OCR.

## Tính năng / Features

✅ **Text Recognition** - Nhận diện văn bản từ ảnh / Extract text from images  
✅ **Multi-line Detection** - Phát hiện nhiều dòng văn bản / Detect multiple text lines  
✅ **Word Segmentation** - Phân tách từng từ / Segment individual words  
✅ **Bounding Boxes** - Vị trí văn bản / Text position coordinates  
✅ **Confidence Scores** - Độ tin cậy (0-1) / Confidence scores (0-1)  
✅ **Text Angle** - Góc xoay văn bản / Text rotation angle  

❌ **Table Recognition** - KHÔNG hỗ trợ / NOT supported  
❌ **Form Processing** - KHÔNG hỗ trợ / NOT supported  

## Sử dụng / Usage

Gửi dữ liệu ảnh dạng binary đến endpoint POST `/`.

Send binary image data to POST `/` endpoint.

## Định dạng hỗ trợ / Supported Formats

- JPEG / JPG
- PNG
- BMP
- Any format supported by PIL/Pillow

## Giới hạn / Limitations

- Kích thước ảnh: 50x50 đến 10000x10000 pixels
- Image size: 50x50 to 10000x10000 pixels
        """,
        version="1.0.11",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "OneOCR Team",
            "url": "https://github.com/OrgGem/oneocr",
        },
        license_info={
            "name": "MIT License",
            "url": "https://github.com/OrgGem/oneocr/blob/main/LICENSE",
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=['*'],
        allow_headers=['*']
    )

    ocr_processor = OcrEngine()

    @app.post(
        '/',
        response_model=OCRResult,
        summary="Nhận diện văn bản từ ảnh / Recognize text from image",
        description="""
Nhận diện văn bản từ hình ảnh và trả về kết quả với thông tin chi tiết.

Recognize text from an image and return detailed results.

## Request / Yêu cầu

Gửi dữ liệu ảnh dạng binary trong request body.  
Send binary image data in the request body.

**Content-Type:** `image/jpeg`, `image/png`, hoặc định dạng ảnh khác / or other image format

## Response / Phản hồi

Trả về JSON chứa:  
Returns JSON containing:

- `text`: Toàn bộ văn bản / Full extracted text
- `text_angle`: Góc xoay văn bản (radians) / Text rotation angle (radians)
- `lines`: Danh sách các dòng văn bản / List of text lines
  - `text`: Nội dung dòng / Line text
  - `bounding_rect`: Tọa độ hộp giới hạn / Bounding box coordinates
  - `words`: Các từ trong dòng / Words in line
    - `text`: Từ / Word
    - `bounding_rect`: Tọa độ từ / Word coordinates
    - `confidence`: Độ tin cậy (0-1) / Confidence score (0-1)

## Example / Ví dụ

### cURL
```bash
curl -X POST "http://localhost:8001/" \\
  -H "Content-Type: image/jpeg" \\
  --data-binary "@image.jpg"
```

### Python
```python
import requests

with open('image.jpg', 'rb') as f:
    response = requests.post('http://localhost:8001/', data=f.read())
    result = response.json()
    print(result['text'])
```
        """,
        responses={
            200: {
                "description": "Nhận diện thành công / Recognition successful",
                "content": {
                    "application/json": {
                        "example": {
                            "text": "Hello World",
                            "text_angle": 0.0,
                            "lines": [
                                {
                                    "text": "Hello World",
                                    "bounding_rect": {
                                        "x1": 10.0, "y1": 10.0,
                                        "x2": 100.0, "y2": 10.0,
                                        "x3": 100.0, "y3": 30.0,
                                        "x4": 10.0, "y4": 30.0
                                    },
                                    "words": [
                                        {
                                            "text": "Hello",
                                            "bounding_rect": {
                                                "x1": 10.0, "y1": 10.0,
                                                "x2": 50.0, "y2": 10.0,
                                                "x3": 50.0, "y3": 30.0,
                                                "x4": 10.0, "y4": 30.0
                                            },
                                            "confidence": 0.99
                                        },
                                        {
                                            "text": "World",
                                            "bounding_rect": {
                                                "x1": 55.0, "y1": 10.0,
                                                "x2": 100.0, "y2": 10.0,
                                                "x3": 100.0, "y3": 30.0,
                                                "x4": 55.0, "y4": 30.0
                                            },
                                            "confidence": 0.98
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            },
            400: {
                "description": "Yêu cầu không hợp lệ / Invalid request",
                "content": {
                    "application/json": {
                        "example": {
                            "text": "",
                            "text_angle": None,
                            "lines": [],
                            "error": "Unsupported image size"
                        }
                    }
                }
            },
            500: {
                "description": "Lỗi xử lý / Processing error",
                "content": {
                    "application/json": {
                        "example": {
                            "text": "",
                            "text_angle": None,
                            "lines": [],
                            "error": "DLL initialization failed"
                        }
                    }
                }
            }
        },
        tags=["OCR"]
    )
    async def process_image(request: Request):
        """
        Xử lý ảnh và trả về kết quả nhận diện văn bản.
        
        Process image and return text recognition results.
        """
        image_data = await request.body()
        image = Image.open(BytesIO(image_data))
        result = ocr_processor.recognize_pil(image)
        return Response(
            content=json.dumps(result, indent=2, ensure_ascii=False),
            media_type='application/json'
        )

    @app.get(
        '/health',
        summary="Kiểm tra trạng thái / Health check",
        description="Kiểm tra xem API có hoạt động không / Check if API is running",
        tags=["Health"]
    )
    async def health_check():
        """Endpoint to check API health"""
        return {"status": "healthy", "service": "OneOCR API", "version": "1.0.11"}

    uvicorn.run(app, host='0.0.0.0', port=8001)

if __name__ == '__main__':
    serve()
