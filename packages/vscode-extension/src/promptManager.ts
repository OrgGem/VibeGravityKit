import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { getSkillsRoot, getWorkspaceRoot, safeSkillDirectoryName } from './config';
import { IDE_TARGETS, resolveWorkspacePath, detectCurrentIdeTargetId } from './ideTargets';
import { NormalizedSkill, SkillInstallTarget } from './types';

export interface PromptFile {
    label: string;
    relativePath: string;
    absolutePath: string;
    category: 'agent' | 'skill' | 'mcp' | 'ide';
    exists: boolean;
    size: number;
    preview: string;
}

const MAX_PROMPT_FILES = 120;
const MAX_PREVIEW_LENGTH = 6000;

export function collectPromptFiles(): PromptFile[] {
    const workspaceRoot = getWorkspaceRoot();
    const files = new Map<string, PromptFile>();

    for (const target of IDE_TARGETS) {
        for (const promptPath of target.promptPaths) {
            addPromptFile(files, workspaceRoot, promptPath, inferCategory(promptPath));
        }

        for (const promptDir of target.promptDirs) {
            addMarkdownFilesFromDirectory(files, workspaceRoot, promptDir, target.id === 'agent' ? 'agent' : 'ide');
        }

        if (target.mcpConfigPath) {
            addPromptFile(files, workspaceRoot, target.mcpConfigPath, 'mcp');
        }
    }

    addSkillMarkdownFiles(files);

    return [...files.values()]
        .sort((left, right) => {
            const categoryOrder = categoryRank(left.category) - categoryRank(right.category);
            return categoryOrder !== 0
                ? categoryOrder
                : left.relativePath.localeCompare(right.relativePath);
        })
        .slice(0, MAX_PROMPT_FILES);
}

export async function openPromptFile(relativePath?: string): Promise<void> {
    const workspaceRoot = getWorkspaceRoot();
    let selectedPath = relativePath;

    if (!selectedPath) {
        const promptFiles = collectPromptFiles();
        const picked = await vscode.window.showQuickPick(
            promptFiles.map((file) => ({
                label: file.label,
                description: file.relativePath,
                detail: file.exists ? `${file.category} prompt` : 'Missing file',
                file
            })),
            {
                title: 'Open prompt or instruction file',
                placeHolder: 'Select a SKILL.md, agent prompt, rule, or MCP config'
            }
        );

        selectedPath = picked?.file.relativePath;
    }

    if (!selectedPath) {
        return;
    }

    const absolutePath = resolveWorkspacePath(workspaceRoot, selectedPath);
    fs.mkdirSync(path.dirname(absolutePath), { recursive: true });

    if (!fs.existsSync(absolutePath)) {
        fs.writeFileSync(absolutePath, createPromptTemplate(selectedPath), 'utf8');
    }

    const document = await vscode.workspace.openTextDocument(vscode.Uri.file(absolutePath));
    await vscode.window.showTextDocument(document, { preview: false });
}

export async function createMainInstructionFile(): Promise<void> {
    const workspaceRoot = getWorkspaceRoot();
    const relativePath = 'AGENTS.md';
    const absolutePath = resolveWorkspacePath(workspaceRoot, relativePath);

    if (fs.existsSync(absolutePath)) {
        await openPromptFile(relativePath);
        return;
    }

    fs.writeFileSync(absolutePath, createPromptTemplate(relativePath), 'utf8');
    await openPromptFile(relativePath);
}

export async function toggleInstructionInPromptFiles(enabled: boolean): Promise<void> {
    const workspaceRoot = getWorkspaceRoot();
    const targetFiles = [
        '.kiro/steering/brain.md',
        'AGENTS.md',
        '.cursorrules',
        '.windsurfrules'
    ];

    const instructionBlock = `
<!-- MCP_SKILL_ROUTER_START -->
> [!IMPORTANT]
> **Skill Routing:** The MCP \`skill-router\` is enabled. You MUST use the \`search_skills\` MCP tool to search for necessary skills when the user gives you a task. If the user explicitly mentions a skill or workflow, use the tool to find it before proceeding.
<!-- MCP_SKILL_ROUTER_END -->
`.trim() + '\n';

    for (const relativePath of targetFiles) {
        const absolutePath = resolveWorkspacePath(workspaceRoot, relativePath);
        if (!fs.existsSync(absolutePath)) {
            continue;
        }

        let content = fs.readFileSync(absolutePath, 'utf8');
        const startTag = '<!-- MCP_SKILL_ROUTER_START -->';
        const endTag = '<!-- MCP_SKILL_ROUTER_END -->';
        
        // Remove existing block if present
        const regex = new RegExp(`[\\s\\n]*${startTag}[\\s\\S]*?${endTag}[\\s\\n]*`, 'g');
        content = content.replace(regex, '\n\n');

        if (enabled) {
            // Append to the top after frontmatter if exists, or just at the top
            if (content.startsWith('---')) {
                const endOfFrontmatter = content.indexOf('---', 3);
                if (endOfFrontmatter !== -1) {
                    content = content.slice(0, endOfFrontmatter + 3) + '\n\n' + instructionBlock + content.slice(endOfFrontmatter + 3);
                } else {
                    content = instructionBlock + '\n' + content;
                }
            } else {
                content = instructionBlock + '\n' + content;
            }
        }

        // Clean up multiple empty lines
        content = content.replace(/\n{3,}/g, '\n\n').trim() + '\n';
        fs.writeFileSync(absolutePath, content, 'utf8');
    }
}

function addSkillMarkdownFiles(files: Map<string, PromptFile>): void {
    let skillsRoot: string;
    try {
        skillsRoot = getSkillsRoot();
    } catch {
        return;
    }

    if (!fs.existsSync(skillsRoot)) {
        return;
    }

    for (const entry of fs.readdirSync(skillsRoot, { withFileTypes: true })) {
        if (!entry.isDirectory() || entry.name.startsWith('.')) {
            continue;
        }

        const skillMarkdownPath = path.join(skillsRoot, entry.name, 'SKILL.md');
        if (!fs.existsSync(skillMarkdownPath)) {
            continue;
        }

        const workspaceRoot = getWorkspaceRoot();
        const relativePath = normalizeRelativePath(path.relative(workspaceRoot, skillMarkdownPath));
        addPromptFile(files, workspaceRoot, relativePath, 'skill');
    }
}

function addMarkdownFilesFromDirectory(
    files: Map<string, PromptFile>,
    workspaceRoot: string,
    relativeDir: string,
    category: PromptFile['category']
): void {
    const absoluteDir = resolveWorkspacePath(workspaceRoot, relativeDir);
    if (!fs.existsSync(absoluteDir)) {
        return;
    }

    const entries = fs.readdirSync(absoluteDir, { withFileTypes: true });
    for (const entry of entries) {
        if (!entry.isFile() || entry.name.startsWith('.')) {
            continue;
        }

        if (!/\.(md|mdc|toml|json)$/i.test(entry.name)) {
            continue;
        }

        addPromptFile(files, workspaceRoot, normalizeRelativePath(path.join(relativeDir, entry.name)), category);
    }
}

function addPromptFile(
    files: Map<string, PromptFile>,
    workspaceRoot: string,
    relativePath: string,
    category: PromptFile['category']
): void {
    const normalizedRelativePath = normalizeRelativePath(relativePath);
    if (files.has(normalizedRelativePath)) {
        return;
    }

    const absolutePath = resolveWorkspacePath(workspaceRoot, normalizedRelativePath);
    const exists = fs.existsSync(absolutePath);
    const stat = exists ? fs.statSync(absolutePath) : undefined;

    files.set(normalizedRelativePath, {
        label: path.basename(normalizedRelativePath),
        relativePath: normalizedRelativePath,
        absolutePath,
        category,
        exists,
        size: stat?.size || 0,
        preview: exists && stat?.isFile() ? readPreview(absolutePath) : ''
    });
}

function inferCategory(relativePath: string): PromptFile['category'] {
    if (/mcp\.json$|config\.toml$/i.test(relativePath)) {
        return 'mcp';
    }

    if (/skill\.md$/i.test(relativePath)) {
        return 'skill';
    }

    return 'agent';
}

function readPreview(filePath: string): string {
    try {
        const raw = fs.readFileSync(filePath, 'utf8');
        if (raw.length <= MAX_PREVIEW_LENGTH) {
            return raw;
        }

        return `${raw.slice(0, MAX_PREVIEW_LENGTH)}\n\n...`;
    } catch {
        return '';
    }
}

function createPromptTemplate(relativePath: string): string {
    const normalized = relativePath.replace(/\\/g, '/');

    if (/\.kiro\/agents\/.*\.md$/i.test(normalized)) {
        const agentName = path.basename(normalized, '.md');
        return [
            `# Agent Role: ${agentName}`,
            '',
            `Bạn là một AI Agent chuyên biệt chịu trách nhiệm thực hiện các tác vụ liên quan đến ${agentName}. Hãy làm việc chặt chẽ với các file hướng dẫn trong thư mục \`.kiro/steering/\` để hoàn thành mục tiêu.`,
            '',
            '## Quy tắc hoạt động (Rules & Behaviors)',
            '- **Định vị & Phạm vi:** Chỉ thực hiện các tác vụ thuộc phạm vi quản lý. Nếu có tác vụ nằm ngoài, hãy chuyển giao hoặc báo cáo lại.',
            '- **Tuân thủ Guidelines:** Luôn đọc file \`.kiro/steering/tech.md\` để nắm rõ coding standards và \`.kiro/steering/product.md\` để hiểu rõ luồng nghiệp vụ trước khi viết mã.',
            '- **Ghi chép Nhật ký:** Luôn ghi chép lại các quyết định thiết kế hoặc thay đổi cấu trúc quan trọng vào Journal.',
            '',
            '## Quy trình xử lý (Execution Workflow)',
            '1. **Phân tích yêu cầu:** Nhận diện phạm vi, kiểm tra kỹ các ràng buộc nghiệp vụ.',
            '2. **Lập kế hoạch (Planning):** Liệt kê các file cần chỉnh sửa hoặc tạo mới trước khi code.',
            '3. **Thực thi (Implementation):** Viết mã sạch, dễ bảo trì, tuân thủ chặt chẽ kiến trúc dự án.',
            '4. **Kiểm thử (Verification):** Tự kiểm tra các trường hợp biên và xử lý lỗi triệt để.',
            '',
            '## Hướng dẫn cụ thể cho tác vụ',
            '- Ưu tiên sử dụng các skill cốt lõi đã cài đặt trong workspace.',
            '- [Nhập yêu cầu chi tiết hoặc mô tả hành vi chuyên biệt ở đây...]',
            ''
        ].join('\n');
    }

    if (/\.kiro\/steering\/product\.md$/i.test(normalized)) {
        return [
            '# Product Steering & Vision',
            '',
            'Tài liệu này định hình tầm nhìn sản phẩm, luồng nghiệp vụ chính, chân dung người dùng (personas) và các tính năng cốt lõi cần xây dựng.',
            '',
            '## Tầm nhìn sản phẩm (Product Vision)',
            '- [Mô tả sản phẩm giải quyết vấn đề gì của khách hàng?]',
            '',
            '## Chân dung người dùng (User Personas)',
            '- **[Vai trò]:** [Mô tả ngắn gọn nhu cầu, hành vi, mục tiêu].',
            '',
            '## Tính năng cốt lõi (Core Features)',
            '1. **[Tính năng 1]:** [Luồng hoạt động, trải nghiệm mong muốn].',
            '2. **[Tính năng 2]:** [Luồng hoạt động, trải nghiệm mong muốn].',
            '',
            '## Tiêu chí nghiệm thu (Acceptance Criteria)',
            '- Trải nghiệm người dùng trực quan, mượt mà.',
            '- Xử lý lỗi thân thiện, bảo mật dữ liệu.',
            ''
        ].join('\n');
    }

    if (/\.kiro\/steering\/tech\.md$/i.test(normalized)) {
        return [
            '# Technical Steering & Architecture',
            '',
            'Tài liệu này hướng dẫn chi tiết về Tech Stack, tiêu chuẩn viết code (Coding Standards), kiến trúc hệ thống và quy tắc phát triển trong dự án.',
            '',
            '## Công nghệ cốt lõi (Tech Stack)',
            '- **Ngôn ngữ:** [TypeScript, Python, Go, etc.]',
            '- **Frameworks:** [React, Next.js, FastAPI, NestJS, etc.]',
            '- **Cơ sở dữ liệu:** [PostgreSQL, Redis, MongoDB, etc.]',
            '',
            '## Quy tắc phát triển (Coding Guidelines)',
            '- **Nguyên tắc Clean Code:** Đặt tên rõ ràng, hàm ngắn gọn tập trung vào một nhiệm vụ duy nhất.',
            '- **Xử lý lỗi (Error Handling):** Bắt buộc xử lý lỗi triệt để, ghi log chi tiết, không nuốt lỗi.',
            '- **TypeScript Strict Mode:** Sử dụng type-safe nghiêm ngặt, tránh tối đa kiểu `any`.',
            '',
            '## Kiến trúc dự án (Architecture Patterns)',
            '- [Mô tả cấu trúc thư mục chính hoặc mô hình Clean/Hexagonal Architecture nếu có].',
            ''
        ].join('\n');
    }

    if (/\.kiro\/steering\/structure\.md$/i.test(normalized) || /\.kiro\/steering\/workflow\.md$/i.test(normalized)) {
        return [
            '# Structure & Workflow Steering',
            '',
            'Tài liệu này định hình cấu trúc thư mục dự án và quy trình phối hợp làm việc giữa các Agent.',
            '',
            '## Cấu trúc thư mục (Directory Structure)',
            '- `packages/`: Chứa các sub-packages hoặc services.',
            '- `src/`: Mã nguồn chính của ứng dụng.',
            '- `.kiro/`: Chứa steering, agents và cấu hình điều phối của Kiro.',
            '',
            '## Quy trình phối hợp (Agent Coordination Flow)',
            '1. **Planner Agent:** Tiếp nhận yêu cầu, phân tích và lên kế hoạch trong `.kiro/specs/`.',
            '2. **Developer Agent:** Thực thi mã nguồn dựa trên Tech Steering.',
            '3. **QA/Reviewer Agent:** Đảm bảo chất lượng code và chạy thử nghiệm.',
            ''
        ].join('\n');
    }

    if (/\.kiro\/steering\/.*\.md$/i.test(normalized)) {
        const steeringName = path.basename(normalized, '.md');
        return [
            `# ${steeringName} Steering`,
            '',
            `Tài liệu định hướng nghiệp vụ hoặc kỹ thuật cho cấu phần ${steeringName}.`,
            '',
            '## Mục tiêu định hướng',
            '- [Mục tiêu 1]',
            '- [Mục tiêu 2]',
            '',
            '## Hướng dẫn chi tiết',
            '[Viết các hướng dẫn điều phối hoặc nguyên tắc cụ thể ở đây...]',
            ''
        ].join('\n');
    }

    if (/\.kiro\/specs\/.*\.md$/i.test(normalized)) {
        const specName = path.basename(normalized, '.md');
        return [
            `# Feature Specification: ${specName}`,
            '',
            `Tài liệu này mô tả chi tiết đặc tả kỹ thuật, thiết kế cơ sở dữ liệu, API Endpoints và danh sách công việc cần làm để xây dựng tính năng ${specName}.`,
            '',
            '## Đặc tả chức năng (Functional Specifications)',
            '- **Mục tiêu:** [Mục tiêu của tính năng này].',
            '- **Luồng hoạt động chính:** [Mô tả chi tiết luồng xử lý].',
            '',
            '## Thiết kế kỹ thuật (Technical Design)',
            '- **Database Schema:**',
            '  ```sql',
            '  -- Thiết kế các bảng mới hoặc quan hệ cơ sở dữ liệu',
            '  ```',
            '- **API Endpoints:**',
            '  - `POST /api/v1/...`: [Mô tả request/response body].',
            '',
            '## Danh sách công việc (Task Checklist)',
            '- [ ] Thiết kế cơ sở dữ liệu và viết file migration.',
            '- [ ] Xây dựng các API Endpoint cốt lõi.',
            '- [ ] Tích hợp giao diện Front-end.',
            '- [ ] Viết Unit Test và kiểm tra chất lượng.',
            ''
        ].join('\n');
    }

    if (/AGENTS\.md$/i.test(normalized)) {
        return [
            '# Agent Instructions',
            '',
            'Use this file for workspace-wide agent behavior, coding standards, and project-specific constraints.',
            '',
            '## Project Rules',
            '',
            '- Keep changes scoped to the requested task.',
            '- Preserve existing user changes.',
            ''
        ].join('\n');
    }

    if (/SKILL\.md$/i.test(normalized)) {
        const skillName = safeSkillDirectoryName(path.basename(path.dirname(normalized)) || 'new-skill');
        return [
            '---',
            `name: ${skillName}`,
            'description: Describe when this skill should be used.',
            '---',
            '',
            `# ${skillName}`,
            '',
            'Add concise activation guidance and the workflow the agent should follow.',
            ''
        ].join('\n');
    }

    return '';
}

function normalizeRelativePath(value: string): string {
    return value.replace(/\\/g, '/');
}

function categoryRank(category: PromptFile['category']): number {
    switch (category) {
        case 'agent':
            return 0;
        case 'skill':
            return 1;
        case 'mcp':
            return 2;
        case 'ide':
            return 3;
    }
}

export async function updateSkillInstructionsAfterInstall(
    target: SkillInstallTarget | undefined,
    skillsInstalled: NormalizedSkill[]
): Promise<void> {
    const workspaceRoot = getWorkspaceRoot();
    
    // 1. Detect active brain and router skills
    // We check newly installed skills, canonical skills folder, and the target installation root
    const searchPaths = new Set<string>();
    try {
        const canonicalSkillsRoot = getSkillsRoot();
        if (canonicalSkillsRoot) {
            searchPaths.add(path.resolve(canonicalSkillsRoot));
        }
    } catch {
        // Ignore if getSkillsRoot() is not configured
    }

    if (target?.rootPath) {
        searchPaths.add(path.resolve(target.rootPath));
    }

    const installedSkillKeys = new Set<string>();
    
    // Add skills being installed right now
    for (const s of skillsInstalled) {
        installedSkillKeys.add(s.id.toLowerCase());
        installedSkillKeys.add(s.name.toLowerCase());
    }

    // Scan all search roots for directories or file rules
    for (const sPath of searchPaths) {
        if (fs.existsSync(sPath)) {
            try {
                const stat = fs.statSync(sPath);
                if (stat.isDirectory()) {
                    const entries = fs.readdirSync(sPath, { withFileTypes: true });
                    for (const entry of entries) {
                        if (entry.name.startsWith('.')) {
                            continue;
                        }
                        if (entry.isDirectory()) {
                            installedSkillKeys.add(entry.name.toLowerCase());
                        } else if (entry.isFile()) {
                            const ext = path.extname(entry.name);
                            if (ext === '.md' || ext === '.mdc') {
                                const baseName = path.basename(entry.name, ext);
                                installedSkillKeys.add(baseName.toLowerCase());
                            }
                        }
                    }
                }
            } catch (e) {
                console.error(`Failed to scan skill path ${sPath}:`, e);
            }
        }
    }

    const hasBrain = [...installedSkillKeys].some(key => key.includes('brain'));
    const hasRouter = [...installedSkillKeys].some(key => key.includes('router'));

    // 2. Generate instruction contents
    // We create a clear instruction block in Vietnamese and English to prioritize local skills.
    let instructionBlock = '<!-- GKT_SKILLS_INSTRUCTIONS_START -->\n';
    instructionBlock += '> [!IMPORTANT]\n';
    instructionBlock += '> **Skill Prioritization / Quy tắc ưu tiên Skill:**\n';
    instructionBlock += '> - **Priority / Ưu tiên:** Always prioritize using the installed skills in the workspace. Read the `SKILL.md` file in each skill folder to follow its specified workflow before doing general tasks.\n';
    instructionBlock += '> - **Ưu tiên hàng đầu:** Luôn ưu tiên sử dụng các skill đã được cài đặt trong workspace. Hãy đọc file `SKILL.md` trong thư mục của từng skill để tuân thủ quy trình làm việc trước khi thực hiện tác vụ chung.\n';

    if (hasBrain && hasRouter) {
        instructionBlock += '> - **Core Skills / Skill cốt lõi:** The core skills `skill-router` and `brain-manager` are installed locally as instructions. Active usage is highly prioritized.\n';
        instructionBlock += '> - **Router Priority:** Before starting any request, ALWAYS read and follow the `skill-router` workflow (in `.kiro/skills/skill-router` or `.agent/skills/skill-router`) to route/find appropriate skills.\n';
        instructionBlock += '> - **Định tuyến Skill:** Trước khi thực hiện bất kỳ yêu cầu nào, BẮT BUỘC phải đọc và làm theo hướng dẫn của `skill-router` để tìm và định tuyến đến skill phù hợp nhất.\n';
        instructionBlock += '> - **Brain Priority:** Use `brain-manager` (in `.kiro/skills/brain-manager` or `.agent/skills/brain-manager`) to query repository guidelines, search knowledge items, and update journals.\n';
        instructionBlock += '> - **Quản lý kiến thức:** Sử dụng `brain-manager` để truy vấn hướng dẫn (Guidelines), tìm kiếm kiến thức (Knowledge Items) và ghi chép nhật ký trước khi thiết kế/lập trình.\n';
        instructionBlock += '> - **No MCP Required / Không cần MCP:** These skills are fully self-contained as instructions; execute them by reading their `SKILL.md` directly. Không cần kích hoạt hay cấu hình MCP cho các skill này.\n';
    } else {
        instructionBlock += '> - **Usage / Hướng dẫn sử dụng:** Find and follow the `SKILL.md` of any matching skill in the workspace skills folder (e.g. `.kiro/skills/` or `.agent/skills/`).\n';
    }
    instructionBlock += '<!-- GKT_SKILLS_INSTRUCTIONS_END -->\n';

    // Formulate a concise tag for JSON files
    let jsonInstructionTag = ' [GKT_SKILLS_INSTRUCTIONS_START: Always prioritize using installed skills. ';
    if (hasBrain && hasRouter) {
        jsonInstructionTag += 'BẮT BUỘC: Hãy luôn sử dụng skill-router để tìm định tuyến skill và dùng brain-manager để quản lý kiến thức/nhật ký trước khi xử lý yêu cầu. Đọc trực tiếp SKILL.md không cần cấu hình MCP. ';
    } else {
        jsonInstructionTag += 'Đọc file SKILL.md trong thư mục từng skill để tuân thủ đúng quy trình làm việc. ';
    }
    jsonInstructionTag += 'GKT_SKILLS_INSTRUCTIONS_END]';

    // 3. Determine if we are installing to Kiro
    const targetId = target?.id;
    const isKiro = targetId === 'kiro';

    if (isKiro) {
        // A. Kiro Agents: Update all .md files in .kiro/agents/
        const agentsDir = path.join(workspaceRoot, '.kiro/agents');
        if (fs.existsSync(agentsDir)) {
            try {
                const files = fs.readdirSync(agentsDir);
                for (const file of files) {
                    if (file.endsWith('.md')) {
                        const filePath = path.join(agentsDir, file);
                        const stat = fs.statSync(filePath);
                        if (!stat.isFile()) {
                            continue;
                        }

                        let content = fs.readFileSync(filePath, 'utf8');
                        
                        // Replace existing block or append to the end
                        const startTag = '<!-- GKT_SKILLS_INSTRUCTIONS_START -->';
                        const endTag = '<!-- GKT_SKILLS_INSTRUCTIONS_END -->';
                        const regex = new RegExp(`[\\s\\n]*${startTag}[\\s\\S]*?${endTag}[\\s\\n]*`, 'g');
                        content = content.replace(regex, '\n\n');
                        
                        content = content.trim() + '\n\n' + instructionBlock;
                        content = content.replace(/\n{3,}/g, '\n\n').trim() + '\n';
                        fs.writeFileSync(filePath, content, 'utf8');
                    }
                }
            } catch (e) {
                console.error('Failed to update Kiro agents:', e);
            }
        }

        // B. Kiro Hooks: Update all .json files in .kiro/hooks/
        const hooksDir = path.join(workspaceRoot, '.kiro/hooks');
        if (fs.existsSync(hooksDir)) {
            try {
                const files = fs.readdirSync(hooksDir);
                for (const file of files) {
                    if (file.endsWith('.json')) {
                        const filePath = path.join(hooksDir, file);
                        const stat = fs.statSync(filePath);
                        if (!stat.isFile()) {
                            continue;
                        }

                        const raw = fs.readFileSync(filePath, 'utf8');
                        const parsed = JSON.parse(raw);
                        
                        if (parsed && typeof parsed.instructions === 'string') {
                            let inst = parsed.instructions;
                            
                            // Remove existing block
                            const startTag = '\\[GKT_SKILLS_INSTRUCTIONS_START:';
                            const endTag = 'GKT_SKILLS_INSTRUCTIONS_END\\]';
                            const regex = new RegExp(`\\s*${startTag}[\\s\\S]*?${endTag}\\s*`, 'g');
                            inst = inst.replace(regex, ' ').trim();
                            
                            // Append new block
                            parsed.instructions = (inst + ' ' + jsonInstructionTag).trim();
                            fs.writeFileSync(filePath, JSON.stringify(parsed, null, 2) + '\n', 'utf8');
                        }
                    }
                }
            } catch (e) {
                console.error('Failed to update Kiro hooks:', e);
            }
        }
    }

    // C. Non-Kiro / Standard prompt files (Strictly Gated)
    const filesToUpdate: string[] = [];
    if (!targetId) {
        // Default target is unspecified: update AGENTS.md, plus the currently active IDE prompt rules if detected
        filesToUpdate.push('AGENTS.md');
        const activeIde = detectCurrentIdeTargetId();
        if (activeIde === 'cursor') {
            filesToUpdate.push('.cursorrules');
        } else if (activeIde === 'windsurf') {
            filesToUpdate.push('.windsurfrules');
        } else if (activeIde === 'cline') {
            filesToUpdate.push('.clinerules');
        }
    } else {
        // Strictly gate prompt writes to the target IDE being installed to
        if (targetId === 'cursor') {
            filesToUpdate.push('.cursorrules');
        } else if (targetId === 'windsurf') {
            filesToUpdate.push('.windsurfrules');
        } else if (targetId === 'cline') {
            filesToUpdate.push('.clinerules');
        } else if (targetId === 'agent' || targetId === 'codex') {
            filesToUpdate.push('AGENTS.md');
        }
    }

    for (const file of filesToUpdate) {
        const filePath = path.join(workspaceRoot, file);
        if (fs.existsSync(filePath)) {
            try {
                const stat = fs.statSync(filePath);
                if (!stat.isFile()) {
                    console.log(`Skipping instruction update for ${file} because it is not a file.`);
                    continue;
                }

                let content = fs.readFileSync(filePath, 'utf8');
                
                const startTag = '<!-- GKT_SKILLS_INSTRUCTIONS_START -->';
                const endTag = '<!-- GKT_SKILLS_INSTRUCTIONS_END -->';
                const regex = new RegExp(`[\\s\\n]*${startTag}[\\s\\S]*?${endTag}[\\s\\n]*`, 'g');
                content = content.replace(regex, '\n\n');
                
                if (content.startsWith('---')) {
                    const endOfFrontmatter = content.indexOf('---', 3);
                    if (endOfFrontmatter !== -1) {
                        content = content.slice(0, endOfFrontmatter + 3) + '\n\n' + instructionBlock + content.slice(endOfFrontmatter + 3);
                    } else {
                        content = instructionBlock + '\n' + content;
                    }
                } else {
                    content = instructionBlock + '\n' + content;
                }
                
                content = content.replace(/\n{3,}/g, '\n\n').trim() + '\n';
                fs.writeFileSync(filePath, content, 'utf8');
            } catch (e) {
                console.error(`Failed to update standard prompt file ${file}:`, e);
            }
        }
    }
}

