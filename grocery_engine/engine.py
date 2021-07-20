import pandas as pd
from recipe_scrapers import scrape_me
import parse_ingredient
import numpy as np
import os
from functools import reduce
import requests
import json

# global variables
recipe_file = "yummy_recipes.xlsx"
additional_items_file = "additional_items.xlsx"
chart_file = "chart_spec.json"
recipe_table_file = "recipe_table.html"
shopping_list_file = "shopping_list.json"

base_data_url = "https://ethanbg2.github.io/meal-plan/data/"


def read_in_recipes(num_recipes):
    os.chdir("..")
    os.chdir("data/")
    urls = pd.read_excel(recipe_file)
    additional_items = pd.read_excel(additional_items_file)
    os.chdir("..")
    os.chdir("grocery_engine/")

    # remove duplicate recipes
    urls.drop_duplicates(subset=["urls"], inplace=True)

    # return a random sample or recipes
    if len(urls) > num_recipes:
        return urls.sample(num_recipes), additional_items
    else:
        return urls, additional_items


def get_additional_ingredient_info(additional_items):
    # parse all additional items
    additional_ingredients = parse_ingredients(additional_items)

    # make sure it's same shape as rest of data
    additional_ingredients["recipe"] = "None"
    additional_ingredients["cook_time"] = "None"
    additional_ingredients["link"] = "None"

    return additional_ingredients


def compile_recipe_info(urls, additional_items):
    dfs = []
    for url in urls:
        scraper = scrape_me(url)
        ingredient_info = parse_ingredients(scraper.ingredients())

        # Add other info
        ingredient_info["recipe"] = scraper.title()
        ingredient_info["cook_time"] = scraper.total_time()
        ingredient_info["link"] = url

        dfs.append(ingredient_info)

    # add additional ingredients to ingredient data
    dfs.append(get_additional_ingredient_info(additional_items))

    return pd.concat(dfs)


def parse_ingredients(ingredients):
    data = []
    for ingredient in ingredients:
        info = (ingredient, np.NaN, np.NaN, np.NaN)
        try:
            info = parse_ingredient.parse(ingredient)
            info = info.as_dict()
        except Exception as e:
            pass
            print(e)
            data.append(info)
            continue

        # puts original ingredient if low confidence
        if info["confidence"] < .04:
            data.append((ingredient, np.NaN, np.NaN, np.NaN))
            continue

        # puts all information together
        data.append((info["product"], info["quantity"], info["unit"], info["usda_info"]["category"]))

    return pd.DataFrame(data, columns=["product", "quantity", "unit", "category"])


def merge_shopping_list(list_):
    quantity = list_.groupby("product").quantity.sum()
    units = list_.groupby("product").unit.unique()
    categories = list_.groupby("product").category.first()
    recipes = list_.groupby("product").recipe.unique()

    # union multiple recipes
    recipes = recipes.str.join(" + ")
    # union multiple units
    units = units.str.join(", ")

    df_merged = reduce(lambda left, right: pd.merge(left, right, left_index=True, right_index=True),
                       [quantity, units, categories, recipes])

    df_merged = df_merged.sort_values(["category"])
    return df_merged.reset_index()


# Updates the chart json based on number of elements in shopping list
def update_chart_height(num_elements, spacing):
    chart = json.loads(requests.get(base_data_url + chart_file).text)
    for table in chart["hconcat"]:
        table["height"] = num_elements * spacing

    os.chdir("..")
    os.chdir("data/")
    with open(chart_file, "w") as outfile:
        json.dump(chart, outfile)
    os.chdir("..")
    os.chdir("grocery_engine/")


def save_updated_shopping_list(shopping_list):
    # Save shopping list data to data folder
    os.chdir("..")
    os.chdir("data/")
    shopping_list.to_json(shopping_list_file, orient="records")
    os.chdir("..")
    os.chdir("grocery_engine/")


def save_recipe_table(full_list):
    recipe_table = full_list.groupby("recipe").apply(lambda df: df.iloc[0]).loc[:, ["cook_time", "link"]]
    recipe_table = recipe_table.reset_index()

    # get rid of additional items that don't belong to recipe
    recipe_table = recipe_table.loc[~(recipe_table.recipe == "None")]

    # save recipe table to data folder
    os.chdir("..")
    os.chdir("data/")
    recipe_table.to_html(recipe_table_file, render_links=True)
    os.chdir("..")
    os.chdir("grocery_engine/")


# compile shopping list
recipe_urls, items = read_in_recipes(2)
full_shopping_list = compile_recipe_info(recipe_urls.urls.to_list(), items.item.to_list())
merged_shopping_list = merge_shopping_list(full_shopping_list)

# save files to correct directories to update my website
save_updated_shopping_list(merged_shopping_list)
save_recipe_table(full_shopping_list)

# update chart specification based on number of elements
update_chart_height(len(merged_shopping_list), 40)
