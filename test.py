# test_parsers.py
import tree_sitter_javascript as ts_js
import tree_sitter_typescript as ts_ts
import tree_sitter_html as ts_html

print("JavaScript:", dir(ts_js))
print("TypeScript:", dir(ts_ts))  
print("HTML:", dir(ts_html))