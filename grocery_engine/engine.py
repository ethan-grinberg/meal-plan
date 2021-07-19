import pandas as pd
from recipe_scrapers import scrape_me
import parse_ingredient
import altair as alt
import numpy as np
import os
from functools import reduce


# TODO make sure it only gets a sample of 3 recipes not all
def read_in_recipes():
    os.chdir("..")
    os.chdir("data/")
    urls = pd.read_excel("yummy_recipes.xlsx")
    os.chdir("..")
    os.chdir("grocery_engine/")

    # remove duplicate recipes
    urls.drop_duplicates(subset=["urls"], inplace=True)
    return urls


def compile_recipe_info(urls):
    dfs = []
    for url in urls:
        scraper = scrape_me(url)
        ingredient_info = parse_ingredients(scraper.ingredients())

        # Add other info
        ingredient_info["recipe"] = scraper.title()
        ingredient_info["cook_time"] = scraper.total_time()
        ingredient_info["link"] = url

        dfs.append(ingredient_info)

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

    # prioritze items part of more recipes
    # s = df_merged.recipe.str.len().sort_values(ascending=False).index
    # df_merged = df_merged.reindex(s)

    df_merged = df_merged.sort_values(["category"])
    return df_merged.reset_index()


def save_updated_shopping_list(shopping_list):
    # Save shopping list data to data folder
    os.chdir("..")
    os.chdir("data/")
    shopping_list.to_json("shopping_list.json", orient="records")
    os.chdir("..")
    os.chdir("grocery_engine/")


def save_recipe_table(full_list):
    recipe_table = full_list.groupby("recipe").apply(lambda df: df.iloc[0]).loc[:, ["cook_time", "link"]]
    recipe_table = recipe_table.reset_index()

    # save recipe table to data folder
    os.chdir("..")
    os.chdir("data/")
    recipe_table.to_html("recipe_table.html", render_links=True)
    os.chdir("..")
    os.chdir("grocery_engine/")


# compile shopping list
full_shopping_list = compile_recipe_info(read_in_recipes().urls.to_list())
merged_shopping_list = merge_shopping_list(full_shopping_list)

# save files to correct directories to update my website
save_updated_shopping_list(merged_shopping_list)
save_recipe_table(full_shopping_list)
