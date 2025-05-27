import re
from typing import Dict, List

def parse_code_file(content: str, language: str) -> Dict:
    """Regex-based parser for frontend languages"""
    
    if language in ['js', 'jsx', 'ts', 'tsx', 'javascript', 'typescript']:
        return parse_js_ts_regex(content, language)
    elif language in ['html', 'htm']:
        return {'imports': [], 'exports': [], 'type': 'template'}
    elif language in ['css', 'scss']:
        return {'imports': [], 'exports': [], 'type': 'stylesheet'}
    elif language == 'json':
        return {'imports': [], 'exports': [], 'type': 'config'}
    else:
        return {'imports': [], 'exports': [], 'type': 'unknown'}

def parse_js_ts_regex(content: str, language: str) -> Dict:
    imports = []
    exports = []
    file_type = "module"
    
    # Parse imports
    import_patterns = [
        r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',  # import ... from 'module'
        r'import\s+[\'"]([^\'"]+)[\'"]',                # import 'module'
        r'require\([\'"]([^\'"]+)[\'"]\)',             # require('module')
    ]
    
    for pattern in import_patterns:
        matches = re.findall(pattern, content)
        imports.extend(matches)
    
    # Parse exports
    export_patterns = [
        r'export\s+default\s+(\w+)',           # export default Name
        r'export\s+(?:const|let|var)\s+(\w+)', # export const name
        r'export\s+function\s+(\w+)',          # export function name
        r'export\s+class\s+(\w+)',             # export class Name
    ]
    
    for pattern in export_patterns:
        matches = re.findall(pattern, content)
        exports.extend(matches)
    
    # Check for default export
    if re.search(r'export\s+default', content):
        exports.append('default')
    
    # Determine file type
    if language in ['jsx', 'tsx'] or 'React' in content or '<' in content:
        file_type = "component"
    elif 'test' in content.lower() or 'spec' in content.lower():
        file_type = "test"
    
    return {
        'imports': list(set(imports)),  # Remove duplicates
        'exports': list(set(exports)),
        'type': file_type
    }