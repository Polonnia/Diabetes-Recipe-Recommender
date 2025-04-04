from neo4j import GraphDatabase
from predict_glucose import predict
from utils.health_score import calculate_health_score
import heapq
import random
from typing import List, Dict, Tuple
import csv
from datetime import datetime

class PriorityRecipe:
    """Wrapper class for recipes to enable priority queue functionality"""
    def __init__(self, name: str, preference_score: float):
        self.name = name
        self.preference_score = preference_score
    
    def __lt__(self, other):
        # We want higher preference scores to have higher priority
        return self.preference_score > other.preference_score

class KnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.staple_queue = []
        self.vegetable_queue = []
        self.protein_queue = []
        self._initialize_queues()

    def close(self):
        self.driver.close()

    def _initialize_queues(self):
        """Initialize the three priority queues by loading recipes from Neo4j"""
        with self.driver.session() as session:
            # 获取所有食谱的基本信息
            recipes = session.run(
                "MATCH (r:Recipe) "
                "RETURN r.name AS name, r.type AS type, r.preference_score AS preference_score"
            ).data()  # 使用.data()立即获取所有结果
            
            for record in recipes:
                recipe_name = record["name"]
                preference_score = record["preference_score"]
                recipe = PriorityRecipe(recipe_name, preference_score)
                
                if record["type"] == "Staple":
                    heapq.heappush(self.staple_queue, recipe)
                else:
                    # 在同一个会话中查询食材类型
                    ingredients = session.run(
                        "MATCH (r:Recipe {name: $recipe_name})-[rel:CONTAINS]->(i) "
                        "RETURN i.type AS type",
                        recipe_name=recipe_name
                    ).data()  # 使用.data()立即获取所有结果
                    
                    # 检查食材类型
                    has_protein = any(ing["type"] == "Protein-rich" for ing in ingredients)
                    has_vegetable = any(ing["type"] == "Vegetable" for ing in ingredients)
                    
                    if has_protein:
                        heapq.heappush(self.protein_queue, recipe)
                    elif has_vegetable:
                        heapq.heappush(self.vegetable_queue, recipe)

    def get_top_recipes(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Get top recipes from all three queues.
        Returns:
            tuple: (top 10 staple recipes, top 10 vegetable recipes, top 10 protein recipes)
        """
        # Get top 10 from each queue
        top_staple = [heapq.heappop(self.staple_queue).name for _ in range(min(10, len(self.staple_queue)))]
        top_vegetable = [heapq.heappop(self.vegetable_queue).name for _ in range(min(10, len(self.vegetable_queue)))]
        top_protein = [heapq.heappop(self.protein_queue).name for _ in range(min(10, len(self.protein_queue)))]
        
        # Push them back to maintain the queue
        for name in top_staple:
            heapq.heappush(self.staple_queue, PriorityRecipe(name, self._get_recipe_score(name)))
        for name in top_vegetable:
            heapq.heappush(self.vegetable_queue, PriorityRecipe(name, self._get_recipe_score(name)))
        for name in top_protein:
            heapq.heappush(self.protein_queue, PriorityRecipe(name, self._get_recipe_score(name)))
            
        return top_staple, top_vegetable, top_protein

    def _get_recipe_score(self, recipe_name: str) -> float:
        """Helper method to get a recipe's current preference score"""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (r:Recipe {name: $name}) RETURN r.preference_score AS score",
                name=recipe_name
            )
            return result.single()["score"]

    def get_recipe_ingredients(self, recipe_name: str) -> List[Dict]:
        """
        Get a recipe's ingredients and their properties.
        """
        with self.driver.session() as session:
            result = session.run(
                "MATCH (r:Recipe {name: $recipe_name})-[rel:CONTAINS]->(i) "
                "RETURN i.name AS name, i.carb AS carb, i.protein AS protein, "
                "i.fat AS fat, i.fiber AS fiber, rel.weight AS weight, labels(i) AS type",
                recipe_name=recipe_name
            )
            return [dict(record) for record in result]

    def calculate_recipe_nutrition(self, recipe_name: str) -> Dict[str, float]:
        """
        Calculate total nutrition for a single recipe.
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

    def calculate_group_nutrition(self, recipe_names: List[str], meal_energy_need: float) -> Tuple[float, Dict[str, float]]:
        """
        Calculate total nutrition for a group of recipes.
        """
        total_nutrition = {"carb": 0, "protein": 0, "fat": 0, "fiber": 0}
        meal_energy = 0

        for recipe_name in recipe_names:
            nutrition = self.calculate_recipe_nutrition(recipe_name)
            meal_energy += nutrition["carb"] * 4 + nutrition["protein"] * 4 + nutrition["fat"] * 9

        ratio = meal_energy_need / meal_energy

        for recipe_name in recipe_names:
            nutrition = self.calculate_recipe_nutrition(recipe_name)
            for key in total_nutrition:
                total_nutrition[key] += nutrition[key] * ratio
        return ratio, total_nutrition

    def recommend_recipes(self, user_data: Dict, meal_type: str = "lunch") -> Tuple[List[str], Dict]:
        """
        Recommend recipes using three priority queues:
        - 1 staple recipe (from staple queue)
        - 1 vegetable recipe (from vegetable queue)
        - 1 protein recipe (from protein queue)
        """
        meal_ratios = {
            "breakfast": 0.3,
            "lunch": 0.4,
            "dinner": 0.3,
        }

        meal_energy_need = user_data["TDEE"] * meal_ratios[meal_type]

        # Get top recipes from all queues
        top_staple, top_vegetable, top_protein = self.get_top_recipes()
        
        health_score = 0.6
        
        while health_score < 0.7:
            # Randomly select 1 from each category's top 10
            staple_recipe = random.choice(top_staple)
            vegetable_recipe = random.choice(top_vegetable) if top_vegetable else random.choice(top_staple)
            protein_recipe = random.choice(top_protein) if top_protein else random.choice(top_staple)
            
            recommendations = [staple_recipe, vegetable_recipe, protein_recipe]
            
            # Calculate nutrition and health scores
            weight_ratio, group_nutrition = self.calculate_group_nutrition(recommendations, meal_energy_need)
            predicted_glucose = predict([
                group_nutrition["carb"],
                group_nutrition["fat"],
                group_nutrition["fiber"],
                user_data["pre_meal_glucose"],
            ])
            
            health_score = calculate_health_score(
                group_nutrition, predicted_glucose, meal_energy_need
            )
            
        return recommendations, {
            "health_score": health_score,
            "PBG": predicted_glucose,
            "carb": group_nutrition["carb"],
            "protein": group_nutrition["protein"],
            "fat": group_nutrition["fat"],
            "fiber": group_nutrition["fiber"]
        }

    def update_pref(self, rating: float, recipe_name: str) -> str:
        """
        Update preference scores for a recipe and its ingredients.
        """
        try:
            rating = float(rating)
            if 0 <= rating <= 10:   
                # Update ingredient preference scores
                with self.driver.session() as session:
                    session.execute_write(
                        lambda tx: tx.run(
                            "MATCH (r:Recipe {name: $name})-[:CONTAINS]->(i:Ingredient) "
                            "SET i.preference_score = (i.preference_score + $rating) / 2",
                            name=recipe_name, rating=rating
                        )
                    )

                with self.driver.session() as session:
                    # Get average ingredient score
                    avg_ingredient_score = session.execute_read(
                        lambda tx: tx.run(
                            "MATCH (r:Recipe {name: $name})-[:CONTAINS]->(i:Ingredient) "
                            "RETURN avg(i.preference_score) AS avg_score",
                            name=recipe_name
                        ).single()["avg_score"]
                    )
                    
                    avg_ingredient_score = avg_ingredient_score or 0.6
                    
                    # Update recipe preference score
                    session.execute_write(
                        lambda tx: tx.run(
                            "MATCH (r:Recipe {name: $name}) "
                            "SET r.preference_score = (r.preference_score + $rating + $avg_ingredient_score) / 3",
                            name=recipe_name, 
                            rating=rating,
                            avg_ingredient_score=avg_ingredient_score
                        )
                    )

                # Update the priority queues
                self._update_recipe_in_queues(recipe_name)
                
                return "感谢您的评分！食谱和食材的偏好评分已更新。"
            else:
                return "评分必须在 0 到 10 之间。"
        except ValueError:
            return "请输入有效的数值。"

    def _update_recipe_in_queues(self, recipe_name: str):
        """Update a recipe's position in the priority queues after score change"""
        new_score = self._get_recipe_score(recipe_name)
        
        # Check which queue the recipe is in and update it
        for queue in [self.staple_queue, self.vegetable_queue, self.protein_queue]:
            for i, recipe in enumerate(queue):
                if recipe.name == recipe_name:
                    queue[i].preference_score = new_score
                    heapq.heapify(queue)  # Re-heapify to maintain order
                    return

    def generate_prompt(self, recommendations: List[str], meal_type: str = "lunch") -> str:
        """
        Generate a prompt for LLM to provide cooking instructions for recommended recipes.
        Includes:
        - Recipe names
        - Ingredients with weights
        - Request for cooking instructions
        
        Args:
            recommendations: List of recommended recipe names
            meal_type: Type of meal (breakfast/lunch/dinner)
        
        Returns:
            str: Concise prompt for LLM focused on cooking instructions
        """
        # Prepare detailed recipes section
        recipes_details = []
        for recipe_name in recommendations:
            ingredients = self.get_recipe_ingredients(recipe_name)
            ingredients_list = "\n".join(
                f"- {ing['name']}: {ing['weight']}g" for ing in ingredients
            )
            
            recipes_details.append(f"""
食谱：{recipe_name}
食材（请严格按照以下重量准备）：
{ingredients_list}
""")

        recipes_section = "\n".join(recipes_details)

        # Create the final prompt
        prompt = f"""请为以下{meal_type}食谱提供详细的烹饪说明：

{recipes_section}

对于每个食谱，请包含以下内容：
1. 详细的步骤说明，确保包含每个食材的具体用量
2. 具体的烹饪方法，包括火候和时间
3. 预计的准备和烹饪时间
4. 注意事项和技巧

请特别注意：
- 必须严格按照提供的食材重量进行准备
- 每个步骤都要明确说明食材的用量
- 使用简洁明了的语言，确保说明清晰易懂
- 将每个食谱的说明单独列出，并以食谱名称作为标题

回答："""
        return prompt

def main():
    uri = "bolt://localhost:7687"  # 数据库地址
    user = "neo4j"  # 数据库用户名
    password = "2winadmin"  # 数据库密码
    # 初始化知识图谱
    kg = KnowledgeGraph(uri, user, password)
    
    # 模拟用户数据
    user_data = {
        "height": 170,
        "weight": 70,
        "age": 45,
        "gender": "male",
        "diabetes_type": "II",
        "pre_meal_glucose": 6.0,
        "TDEE": 1800,
        "activity level": "moderately_active"
    }
    
    # 创建结果记录列表
    results = []
    
    # 模拟30次推荐（每次3个食谱）
    for i in range(30):
        print(f"\n=== 第 {i+1} 次推荐 ===")
        
        # 获取推荐
        recommendations, scores = kg.recommend_recipes(user_data)
        
        # 记录结果
        for recipe_name in recommendations:
            while True:  # 循环直到输入有效
                try:
                    # 尝试将输入转换为浮点数
                    rating = float(input(f"请为食谱 '{recipe_name}' 评分(0-10): "))
                    # 检查范围
                    if 0 <= rating <= 10:
                        break  # 输入有效，退出循环
                    else:
                        print("评分必须在0-10之间！")
                except ValueError:  # 捕获非数字输入错误
                    print("请输入数字！")
            
            # 更新偏好评分
            kg.update_pref(rating, recipe_name)
            
            # 记录结果
            results.append({
                "iteration": i+1,
                "recipe_name": recipe_name,
                "health_score": scores["health_score"],
                "glucose_score": scores["glucose_score"],
                "nutrient_score": scores["nutrient_score"],
                "user_rating": rating,
                "preference_score": None  # 将在下面获取
            })
            
        print(f"健康评分: {scores['health_score']:.2f}")
        print(f"血糖评分: {scores['glucose_score']:.2f}")
        print(f"营养评分: {scores['nutrient_score']:.2f}")
    
    # 获取最终的preference_score
    with kg.driver.session() as session:
        for record in results:
            pref_score = session.run(
                "MATCH (r:Recipe {name: $name}) RETURN r.preference_score AS score",
                name=record["recipe_name"]
            ).single()["score"]
            record["preference_score"] = pref_score
    
    # 关闭数据库连接
    kg.close()
    
    # 将结果保存为CSV文件
    filename = "recommendation_results.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['iteration', 'recipe_name', 
                    'health_score', 'glucose_score', 'nutrient_score',
                    'user_rating', 'preference_score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n测试完成，结果已保存到 {filename}")

if __name__ == "__main__":
    main()