---
name: meta-thinker
description: Creative idea advisor. Brainstorm frameworks, product archetypes, industry data, and monetization models. Zero-token data retrieval via script.
---

# Meta Thinker Skill

## Overview
Cung cấp data phong phú cho quá trình brainstorm và phát triển ý tưởng.
Thay vì tốn token để "nghĩ", agent dùng script để truy xuất data có sẵn.

## Data Files

| File | Nội dung | Entries |
| :--- | :--- | :---: |
| `data/brainstorm_frameworks.json` | 10 creative frameworks (SCAMPER, Lean Canvas...) | 10 |
| `data/product_archetypes.json` | 20 mẫu sản phẩm + examples | 20 |
| `data/industry_database.json` | 25 ngành + pain points + opportunities | 25 |
| `data/feature_ideas.json` | 200+ feature ideas theo category | 200+ |
| `data/monetization_models.json` | 12 mô hình kiếm tiền + examples | 12 |
| `data/platform_guide.json` | 6 platforms + pros/cons + tech stacks | 6 |

## Script Usage

```bash
# Tìm ý tưởng theo domain
python scripts/idea_engine.py --domain "food-delivery" --query "healthy"

# Lấy features cho một loại sản phẩm
python scripts/idea_engine.py --archetype "marketplace" --platform "mobile"

# Tìm monetization phù hợp
python scripts/idea_engine.py --monetization --domain "education"

# Brainstorm framework gợi ý
python scripts/idea_engine.py --framework "lean-canvas" --context "fitness app"
```

## Output
Script trả về JSON compact, agent chỉ cần đọc và trình bày cho user.
Tiết kiệm ~90% token so với việc tự brainstorm không có data.
