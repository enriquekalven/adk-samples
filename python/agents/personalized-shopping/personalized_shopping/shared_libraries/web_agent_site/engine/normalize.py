import re
COLOR_SET = ['alabaster', 'apricot', 'aqua', 'ash', 'asphalt', 'azure', 'banana', 'beige', 'black', 'blue', 'blush', 'bordeaux', 'bronze', 'brown', 'burgundy', 'camel', 'camo', 'caramel', 'champagne', 'charcoal', 'cheetah', 'chestnut', 'chocolate', 'christmas', 'coffee', 'cognac', 'copper', 'coral', 'cranberry', 'cream', 'crystal', 'dark', 'denim', 'eggplant', 'elephant', 'espresso', 'fuchsia', 'gold', 'granite', 'grape', 'graphite', 'grass', 'gray', 'green', 'grey', 'heather', 'indigo', 'ivory', 'ivy', 'khaki', 'lavender', 'lemon', 'leopard', 'light', 'lilac', 'lime', 'magenta', 'maroon', 'mauve', 'merlot', 'midnight', 'mint', 'mocha', 'multicolor', 'mushroom', 'mustard', 'natural', 'navy', 'nude', 'olive', 'orange', 'peach', 'pewter', 'pink', 'plum', 'purple', 'rainbow', 'red', 'rose', 'royal', 'rust', 'sand', 'sapphire', 'seashell', 'silver', 'skull', 'slate', 'steel', 'stone', 'stonewash', 'sunflower', 'tan', 'taupe', 'teal', 'tiger', 'turquoise', 'violet', 'walnut', 'wheat', 'white', 'wine', 'yellow']
SIZE_SET = ['xx-large', '3x-large', '4x-large', '5x-large', 'x-large', 'x-small', 'medium', 'large', 'small', 'queen', 'twin', 'full', 'king', 'one size', 'pack']
SIZE_PATTERNS = [re.compile('(.*)neck(.*)sleeve'), re.compile('(.*) women \\| (.*) men'), re.compile('(.*)w x(.*)l'), re.compile('(.*)w by (.*)l'), re.compile('(.*)w x(.*)h'), re.compile('(.*)wide'), re.compile('(.*)x-wide'), re.compile('(.*)narrow'), re.compile('(.*)petite'), re.compile('(.*)inch'), re.compile('(.*)plus'), re.compile('(.*)mm'), re.compile('women(.*)'), re.compile('(.*)x(.*)'), re.compile('(.*)ft'), re.compile('(.*)feet'), re.compile('(.*)meter'), re.compile('(.*)yards'), re.compile('(.*)\\*(.*)'), re.compile('(.*)\\-(.*)'), re.compile('(\\d+)"$'), re.compile('(\\d+)f$'), re.compile('(\\d+)m$'), re.compile('(\\d+)cm$'), re.compile('(\\d+)g$')]
SIZE_PATTERNS = [re.compile(s) for s in SIZE_SET] + SIZE_PATTERNS

def normalize_color(color_string: str) -> str:
    """Extracts the first color found if exists"""
    for norm_color in COLOR_SET:
        if norm_color in color_string:
            return norm_color
    return color_string

def normalize_color_size(product_prices: dict) -> tuple[dict, dict]:
    """Get mappings of all colors, sizes to corresponding values in COLOR_SET, SIZE_PATTERNS"""
    all_colors, all_sizes = (set(), set())
    for (_, color, size), _ in product_prices.items():
        all_colors.add(color.lower())
        all_sizes.add(size.lower())
    color_mapping = {'N.A.': 'not_matched'}
    for c in all_colors:
        matched = False
        for base in COLOR_SET:
            if base in c:
                color_mapping[c] = base
                matched = True
                break
        if not matched:
            color_mapping[c] = 'not_matched'
    size_mapping = {'N.A.': 'not_matched'}
    for s in all_sizes:
        matched = False
        for pattern in SIZE_PATTERNS:
            m = re.search(pattern, s)
            if m is not None:
                matched = True
                size_mapping[s] = pattern.pattern
                break
        if not matched:
            if s.replace('.', '', 1).isdigit():
                size_mapping[s] = 'numeric_size'
                matched = True
        if not matched:
            size_mapping[s] = 'not_matched'
    return (color_mapping, size_mapping)