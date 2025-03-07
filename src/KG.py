from neo4j import GraphDatabase
from predict_glucose import predict_glucose
from utils.health_score import calculate_health_score
import random

class KnowledgeGraph:
    uri = "bolt://localhost:7687"  # 数据库地址
    user = "neo4j"  # 数据库用户名
    password = "your_password"  # 数据库密码

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_recipes(self):
        """
        从 Neo4j 获取所有 preference_score >= 0.6 的食谱及其偏好评分。
        """
        with self.driver.session() as session:
            result = session.run(
                "MATCH (r:Recipe) WHERE r.preference_score >= 0.6 "
                "RETURN r.name AS name, r.preference_score AS preference_score"
            )
            recipes = [record["name"] for record in result]
            return recipes

    def get_recipe_ingredients(self, recipe_name):
        """
        获取食谱的食材及其重量。
        """
        with self.driver.session() as session:
            result = session.run(
                "MATCH (r:Recipe {name: $name})-[:CONTAINS]->(i) "
                "RETURN i.name AS name, i.carb AS carb, i.protein AS protein, i.fat AS fat, i.fiber AS fiber, r.CONTAINS.weight AS weight, labels(i) AS type",
                name=recipe_name
            )
            ingredients = [dict(record) for record in result]
            return ingredients

    def calculate_recipe_nutrition(self, recipe_name):
        """
        计算单个食谱的总营养成分。
        """
        ingredients = self.get_recipe_ingredients(recipe_name)
        total_carb = sum(i["carb"] * i["weight"] / 100 for i in ingredients)
        total_protein = sum(i["protein"] * i["weight"] / 100 for i in ingredients)
        total_fat = sum(i["fat"] * i["weight"] / 100 for i in ingredients)
        total_fiber = sum(i["fiber"] * i["weight"] / 100 for i in ingredients)

        return {
            "carb": total_carb,
            "protein": total_protein,
            "fat": total_fat,
            "fiber": total_fiber
        }

    def calculate_group_nutrition(self, recipe_names):
        """
        计算一组食谱的总营养成分。
        """
        total_nutrition = {"carb": 0, "protein": 0, "fat": 0, "fiber": 0}
        for recipe_name in recipe_names:
            nutrition = self.calculate_recipe_nutrition(recipe_name)
            for key in total_nutrition:
                total_nutrition[key] += nutrition[key]
        return total_nutrition

    def recommend_recipes(self, user_data, meal_type):
        """
        推荐适合用户的食谱组合，确保包含 Meat、Vegetable 和 Staple。
        """
        # 从 Neo4j 获取食谱
        recipes = self.get_recipes()
        health_score = 0.6
        # 筛选包含 Meat、Vegetable 和 Staple 的食谱组合
        while health_score <= 0.7:
            recommendations = []
            meat_added = False
            vegetable_added = False
            staple_added = False

            # 随机打乱食谱顺序
            random.shuffle(recipes)

            for recipe in recipes:

                ingredients = self.get_recipe_ingredients(recipe)
                types = set()

                for ingredient in ingredients:
                    types.update(ingredient["type"])

                if not meat_added and "Meat" in types:
                    recommendations.append(recipe)
                    meat_added = True
                elif not vegetable_added and "Vegetable" in types:
                    recommendations.append(recipe)
                    vegetable_added = True
                elif not staple_added and "Staple" in types:
                    recommendations.append(recipe)
                    staple_added = True
                elif len(recommendations) >= 3:
                    break
                else:
                    recommendations.append(recipe)

                if len(recommendations) >= 3:
                    break

                # 计算一组食谱的总营养成分
                group_nutrition = self.calculate_group_nutrition(recommendations)

                # 计算一组食谱的总健康评分
                predicted_glucose = predict_glucose(
                    user_data["pre_meal_glucose"],
                    group_nutrition["carb"],
                    group_nutrition["fat"],
                    group_nutrition["fiber"],
                    user_data["pre_meal_insulin"]
                )
                health_score = calculate_health_score(user_data, group_nutrition, predicted_glucose, meal_type)

        return recommendations
    
    def update_pref(self, rating, recipe_name): 
        """
        处理用户评分和餐后血糖输入
        """
        # 更新食谱评分
        try:
            rating = float(rating)
            if 0 <= rating <= 10:
                # 更新食谱的 preference_score
                with self.driver.session() as session:
                    session.execute_write(
                        lambda tx: tx.run(
                            "MATCH (r:Recipe {name: $name}) "
                            "SET r.preference_score = (r.preference_score + $rating) / 2",
                            name=recipe_name, rating=rating
                        )
                    )
                
                # 更新食材的 preference_score
                with self.driver.session() as session:
                    session.execute_write(
                        lambda tx: tx.run(
                            "MATCH (r:Recipe {name: $name})-[:CONTAINS]->(i:Ingredient) "
                            "SET i.preference_score = (i.preference_score + $rating) / 2",
                            name=recipe_name, rating=rating
                        )
                    )

                return "感谢您的评分！食谱和食材的偏好评分已更新。"
            else:
                return "评分必须在 0 到 10 之间。"
        except ValueError:
            return "请输入有效的数值。"

    @staticmethod
    def _add_recipe(tx, name, preference_score):
        tx.run("CREATE (r:Recipe {name: $name, preference_score: $preference_score})",
               name=name, preference_score=preference_score)

    @staticmethod
    def _add_ingredient(tx, name, preference_score, carb, protein, fat, fiber, ingredient_type):
        tx.run(f"CREATE (i:{ingredient_type} {{name: $name, preference_score: $preference_score, carb: $carb, protein: $protein, fat: $fat, fiber: $fiber}})",
               name=name, preference_score=preference_score, carb=carb, protein=protein, fat=fat, fiber=fiber)

    @staticmethod
    def _add_contains_relationship(tx, recipe_name, ingredient_name, weight):
        tx.run("MATCH (r:Recipe {name: $recipe_name}), (i {name: $ingredient_name}) "
               "CREATE (r)-[:CONTAINS {weight: $weight}]->(i)",
               recipe_name=recipe_name, ingredient_name=ingredient_name, weight=weight)