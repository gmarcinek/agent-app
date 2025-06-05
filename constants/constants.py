LANGUAGE_MAP = {
    # Web frontend
    ".tsx": "tsx", ".ts": "typescript", ".js": "javascript", ".jsx": "jsx",
    ".html": "html", ".htm": "html", ".css": "css", ".scss": "scss", 
    ".sass": "sass", ".less": "less", ".vue": "vue", ".svelte": "svelte",
    
    # Backend
    ".py": "python", ".pyw": "python", ".pyi": "python",
    ".java": "java", ".c": "c", ".cpp": "cpp", ".cs": "csharp",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
    ".swift": "swift", ".kt": "kotlin", ".scala": "scala",
    
    # Config & Data
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".xml": "xml", ".ini": "ini", ".cfg": "config", ".conf": "config",
    ".env": "env", ".properties": "properties",
    
    # Documentation
    ".md": "markdown", ".rst": "rst", ".txt": "text",
    ".tex": "latex", ".adoc": "asciidoc",
    
    # Database
    ".sql": "sql", ".psql": "sql", ".mysql": "sql",
    
    # Shell
    ".sh": "bash", ".bash": "bash", ".zsh": "zsh", ".fish": "fish",
    
    # Other
    ".dockerfile": "dockerfile", ".log": "log"
}

TEXT_EXTENSIONS = {
    # Core web
    ".ts", ".tsx", ".js", ".jsx", ".html", ".css", ".scss",
    ".vue", ".svelte",
    
    # Backend
    ".py", ".java", ".go", ".rs", ".rb", ".php", ".cs",
    
    # Config
    ".json", ".yaml", ".yml", ".toml", ".env", ".ini",
    ".gitignore", ".dockerignore",
    
    # Docs
    ".md", ".txt", ".rst",
    
    # SQL
    ".sql",
    
    # Shell
    ".sh", ".bash"
}

# Pliki bez rozszerzenia, które są zwykle tekstowe
COMMON_TEXT_FILES = {
    "README", "LICENSE", "CHANGELOG", "CONTRIBUTING", "AUTHORS", "COPYING",
    "INSTALL", "NEWS", "TODO", "MANIFEST", "Dockerfile", "Makefile", "Rakefile",
    "Gemfile", "Pipfile", "requirements", "setup", "pyproject", "poetry",
    "package", "composer", "bower", "yarn", "webpack", "rollup", "vite",
    "tsconfig", "jsconfig", "eslint", "prettier", "babel", "jest"
}


IGNORED_DIRS = {"node_modules", ".git", ".meta", "__pycache__", ".vscode", ".idea", "dist", "build", "coverage"}

# Dodaj ignorowane pliki
IGNORED_FILES = {
    # Lock files
    "package-lock.json", 
    "yarn.lock", 
    "pnpm-lock.yaml",
    "composer.lock",
    "Pipfile.lock",
    "poetry.lock",
    
    # Config files
    ".gitignore",
    ".gitattributes", 
    ".editorconfig",
    ".prettierrc",
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.json",
    ".babelrc",
    ".npmrc",
    ".yarnrc",
    
    # Environment files
    ".env",
    ".env.local",
    ".env.development", 
    ".env.production",
    ".env.test",
    
    # TypeScript configs
    "tsconfig.json",
    "tsconfig.base.json",
    "tsconfig.build.json",
    "jsconfig.json",
    
    # Build configs  
    "webpack.config.js",
    "vite.config.js",
    "rollup.config.js",
    "next.config.js",
    "nuxt.config.js",
    "vue.config.js",
    "angular.json",
    "eslint.config.js",
    "README.md",
    "vite-env.d.ts",
    "vite.config.ts",
    "tsconfig.node.json",
    "tsconfig.app.json",
    
    # Other
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini"
}

# Wzorce dla plików zaczynających się od kropki
IGNORED_PATTERNS = {
    ".git",      # .gitignore, .github, etc  
    ".env",      # .env*, .envrc
    ".npm",      # .npmrc, .npmignore
    ".yarn",     # .yarnrc, .yarnignore  
    ".eslint",   # .eslintrc*
    ".prettier", # .prettierrc*
    ".babel",    # .babelrc*
    ".docker",   # .dockerignore
    ".helm",     # .helmignore
    ".vs",       # .vscode, .vs
}