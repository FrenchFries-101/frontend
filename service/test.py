from service.api_word import get_categories
from service.api_word import get_subcategories
from service.api_word import get_words
from service.api_forum import get_posts

data = get_posts()
print(data)
print(get_categories())
print( get_subcategories(2))
print(get_words(3))