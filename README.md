# [Meal Planner](https://ethanbg2.github.io/meal-plan/)
## Features
- turn recipes you find online into shopping lists
- Merge the quantities of an ingredient that is part of multiple recipes, so you know exactly how much to buy
- Sort by category of ingredient for efficient shopping routes
- Interactive shopping list, so you can see what recipe each ingredient is a part of
- You can also add ingredients that aren't part of a recipe to your shopping list

![tutorial](https://user-images.githubusercontent.com/73128220/142785221-431f7019-bd3b-44a8-94b7-a9f083b7a933.gif)

## How to use
- clone this repository
- pip install all dependencies
- edit the excel spreadsheet `yummy_recipes.xlsx` in `data` directory. Put the recipes you want for your this weeks shopping list in the `recipes` sheet. Put any additional items that aren't part of recipes in the `additional` sheet. You can also maintain all the recipes and additional items to eventually pick from in the `all_additional_items` and `all_recipes` sheet.
- cd into the `grocery_engine` directory and run `python engine.py`
- run `git commit -a -m "updated recipe list"`
- run `git push`
- this should update your personal shopping list website at `index.html`. Just make sure you set up your personal github pages for your cloned meal-plan repository.
