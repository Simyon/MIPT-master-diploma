import os
import re
import yaml

def parse_latex_field(text, field):
    """Извлекает значение поля \field {текст} или \field текст"""
    match = re.search(rf'\\{field}\s+{{?(.*?)}}?(?=\s*\\|\s*$)', text, re.DOTALL)
    return match.group(1).strip() if match else None

def build_gost(data):
    """Собирает строку по ГОСТу из словаря полей"""
    res = f"{data.get('authors', '')} {data.get('paper', '') or data.get('book', '')} // "
    if data.get('journal'):
        res += f"{data['journal']}. "
    if data.get('year'):
        res += f"{data['year']}. "
    if data.get('volume'):
        res += f"Т. {data['volume']}. "
    if data.get('issue'):
        res += f"№ {data['issue']}. "
    if data.get('pages'):
        res += f"С. {data['pages']}."
    return res.strip()

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Ищем блок библиографии
    bib_match = re.search(r'\\begin{thebibliography}.*?\\end{thebibliography}', content, re.DOTALL)
    if not bib_match:
        return

    # Разбиваем на отдельные записи по \bibitem или \RBibitem
    items = re.split(r'\\(?:R)?Bibitem\{.*?\}', bib_match.group(0))[1:]
    
    results = []
    for item in items:
        # Разделяем на оригинал и перевод
        parts = re.split(r'\\(?:r)?transl', item)
        
        entry = {}
        # Парсим основную часть
        main_data = {
            "authors": parse_latex_field(parts[0], "by"),
            "paper": parse_latex_field(parts[0], "paper"),
            "book": parse_latex_field(parts[0], "book"),
            "journal": parse_latex_field(parts[0], "jour"),
            "year": parse_latex_field(parts[0], "yr"),
            "volume": parse_latex_field(parts[0], "vol"),
            "issue": parse_latex_field(parts[0], "issue"),
            "pages": parse_latex_field(parts[0], "pages")
        }
        entry.update(main_data)
        entry["raw_bible"] = build_gost(main_data)

        # Если есть перевод
        if len(parts) > 1:
            trans_data = {
                "authors": parse_latex_field(parts[1], "by"),
                "paper": parse_latex_field(parts[1], "paper"),
                "book": parse_latex_field(parts[1], "book"),
                "journal": parse_latex_field(parts[1], "jour"),
                "year": parse_latex_field(parts[1], "yr"),
                "volume": parse_latex_field(parts[1], "vol"),
                "issue": parse_latex_field(parts[1], "issue"),
                "pages": parse_latex_field(parts[1], "pages")
            }
            entry["translated"] = trans_data
            entry["translated"]["raw_bible"] = build_gost(trans_data)

        results.append(entry)

    # Сохраняем в YAML
    output_path = filepath.replace("_utf8.tex", "_biblo.yaml")
    with open(output_path, 'w', encoding='utf-8') as y:
        yaml.dump(results, y, allow_unicode=True, sort_keys=False)

# Обход всех папок
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('_utf8.tex'):
            print(f"Processing {file}...")
            process_file(os.path.join(root, file))
