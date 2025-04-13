from neo4j import GraphDatabase
from predict_glucose import predict
from utils.health_score import calculate_health_score
import heapq
import random
from typing import List, Dict, Tuple
# import csv
# from datetime import datetime

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

    def get_recipe_ingredients(self, recipe_name: str, ratio: float = 1.0) -> List[Dict]:
        """
        Get a recipe's ingredients and their properties.
        Args:
            recipe_name: Name of the recipe
            ratio: Scaling factor for ingredient weights (default: 1.0)
        Returns:
            List of dictionaries containing ingredient information with adjusted weights
        """
        try:
            with self.driver.session() as session:
                result = session.run(
                    "MATCH (r:Recipe {name: $recipe_name})-[rel:CONTAINS]->(i) "
                    "RETURN i.name AS name, i.carb AS carb, i.protein AS protein, "
                    "i.fat AS fat, i.fiber AS fiber, rel.weight AS weight, labels(i) AS type",
                    recipe_name=recipe_name
                )
                ingredients = [dict(record) for record in result]
                
                # 确保所有数值都是原生 Python float 类型
                for ingredient in ingredients:
                    original_weight = ingredient['weight']
                    adjusted_weight = int(original_weight * float(ratio))
                    
                    ingredient['weight'] = adjusted_weight
                    ingredient['carb'] = float(ingredient.get('carb', 0))
                    ingredient['protein'] = float(ingredient.get('protein', 0))
                    ingredient['fat'] = float(ingredient.get('fat', 0))
                    ingredient['fiber'] = float(ingredient.get('fiber', 0))
                
                return ingredients
                
        except Exception as e:
            print(f"获取食谱食材时出错: {str(e)}")
            raise e

    def calculate_recipe_nutrition(self, recipe_name: str) -> Dict[str, float]:
        """
        Calculate total nutrition for a single recipe.
        """
        ingredients = self.get_recipe_ingredients(recipe_name, 1.0)
        total_carb = sum(i["carb"] * i["weight"] / 100 for i in ingredients)
        total_protein = sum(i["protein"] * i["weight"] / 100 for i in ingredients)
        total_fat = sum(i["fat"] * i["weight"] / 100 for i in ingredients)
        total_fiber = sum(i["fiber"] * i["weight"] / 100 for i in ingredients)

        nutrition = {
            "carb": total_carb,
            "protein": total_protein,
            "fat": total_fat,
            "fiber": total_fiber
        }
        return nutrition


    def calculate_group_nutrition(self, recipes, nutrient_needs):
        """
        计算一组食谱的总营养成分，根据营养素需求分别计算每个食谱的缩放比例
        """
        try:
            # 1. 计算每个食谱的原始营养值
            recipe_nutritions = []
            for recipe in recipes:
                nutrition = self.calculate_recipe_nutrition(recipe)
                recipe_nutritions.append(nutrition)
            
            # 2. 计算每个食谱的缩放比例
            ratios = [0.0, 0.0, 0.0]
            
            # 2.1 计算主食和蔬菜的碳水比例
            total_carb = recipe_nutritions[0]["carb"] + recipe_nutritions[1]["carb"] + recipe_nutritions[2]["carb"]
            if total_carb > 0:
                carb_ratio = nutrient_needs["carb"] / total_carb
                ratios[0] = carb_ratio * 0.6  # 主食比例
                ratios[1] = carb_ratio * 0.5
            else:
                ratios[0] = 1.0
                ratios[1] = 1.0
            # 2.2 计算蛋白质食谱和蔬菜的蛋白质比例
            total_protein = recipe_nutritions[1]["protein"] + recipe_nutritions[2]["protein"]
            if total_protein > 0:
                protein_ratio = nutrient_needs["protein"] / total_protein
                ratios[1] += protein_ratio * 0.5  # 蔬菜比例取碳水比例和蛋白质比例中的较大值
                ratios[2] += protein_ratio * 0.8

            total_fat = recipe_nutritions[1]["fat"] + recipe_nutritions[2]["fat"]
            if total_fat > 0:
                fat_ratio = nutrient_needs["fat"] / total_fat
                ratios[1] = min(ratios[1], fat_ratio)
                ratios[2] = min(ratios[2], fat_ratio)
            else:
                ratios[2] = 1.0
            
            # 3. 计算调整后的总营养值
            total_nutrition = {
                "energy": 0.0,
                "carb": 0.0,
                "protein": 0.0,
                "fat": 0.0,
                "fiber": 0.0
            }
            
            for i, nutrition in enumerate(recipe_nutritions):
                ratio = ratios[i]
                total_nutrition["energy"] += float(
                    nutrition["carb"] * 4 * ratio + 
                    nutrition["protein"] * 4 * ratio + 
                    nutrition["fat"] * 9 * ratio
                )
                total_nutrition["carb"] += float(nutrition["carb"] * ratio)
                total_nutrition["protein"] += float(nutrition["protein"] * ratio)
                total_nutrition["fat"] += float(nutrition["fat"] * ratio)
                total_nutrition["fiber"] += float(nutrition["fiber"] * ratio)
            
            return ratios, total_nutrition
            
        except Exception as e:
            print(f"计算群组营养时出错: {str(e)}")
            raise e

    def recommend_recipes(self, user_data: Dict, meal_type: str = "lunch") -> Tuple[List[str], Dict]:
        """
        Recommend recipes using three priority queues:
        - 1 staple recipe (from staple queue)
        - 1 vegetable recipe (from vegetable queue)
        - 1 protein recipe (from protein queue)
        """
        nutrient_needs = user_data["nutrient_needs"][meal_type]
        print(f"Nutrient needs: {nutrient_needs}")

        # Get top recipes from all queues
        top_staple, top_vegetable, top_protein = self.get_top_recipes()
        
        health_score = 0.6
        
        best_recommendations = None
        best_ratios = None
        best_scores = None
        max_attempts = 100  # 防止无限循环
        attempts = 0
        
        while health_score < 0.7 and attempts < max_attempts:
            attempts += 1
            # Randomly select 1 from each category's top 10
            staple_recipe = random.choice(top_staple)
            vegetable_recipe = random.choice(top_vegetable) if top_vegetable else random.choice(top_staple)
            protein_recipe = random.choice(top_protein) if top_protein else random.choice(top_staple)
            
            recommendations = [staple_recipe, vegetable_recipe, protein_recipe]
            
            # Calculate nutrition and health scores
            ratios, group_nutrition = self.calculate_group_nutrition(recommendations, nutrient_needs)
            predicted_glucose = predict([
                group_nutrition["carb"],
                group_nutrition["fat"],
                group_nutrition["fiber"],
                user_data["pre_meal_glucose"],
            ])
            
            health_score = calculate_health_score(
                group_nutrition, predicted_glucose, nutrient_needs
            )
            
            if health_score >= 0.7:
                best_recommendations = recommendations
                best_ratios = ratios
                best_scores = {
                    "health_score": float(health_score),
                    "energy": float(group_nutrition["energy"]),
                    "PBG": float(predicted_glucose[1]),
                    "carb": float(group_nutrition["carb"]),
                    "protein": float(group_nutrition["protein"]),
                    "fat": float(group_nutrition["fat"]),
                    "fiber": float(group_nutrition["fiber"])
                }
        
        # 如果没有找到健康分数>=0.7的组合，使用最后一次计算的结果
        if best_recommendations is None:
            best_recommendations = recommendations
            best_ratios = ratios
            best_scores = {
                "health_score": float(health_score),
                "energy": float(group_nutrition["energy"]),
                "PBG": float(predicted_glucose[1]),
                "carb": float(group_nutrition["carb"]),
                "protein": float(group_nutrition["protein"]),
                "fat": float(group_nutrition["fat"]),
                "fiber": float(group_nutrition["fiber"])
            }
            
        return best_recommendations, best_ratios, best_scores

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

    def generate_prompt(self, recommendations: List[str], meal_type: str = "lunch", ratios: List[float] = [1.0, 1.0, 1.0]) -> str:
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
        for i, recipe_name in enumerate(recommendations):
            ingredients = self.get_recipe_ingredients(recipe_name, ratios[i])
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
        "pre_meal_glucose": 6.0,
        "TDEE": 1800,
        "activity level": "moderately_active",
        "nutrient_needs": {
        "breakfast": {
            "carb": 68,
            "protein": 27,
            "fat": 18
        },
        "lunch": {
            "carb": 90,
            "protein": 36,
            "fat": 24
        },
        "dinner": {
            "carb": 68,
            "protein": 27,
            "fat": 18
        }
}
    }   
   
    # 获取推荐
    recommendations, ratios, nutrition = kg.recommend_recipes(user_data)
    for i, recipe in enumerate(recommendations):
        result = kg.get_recipe_ingredients(recipe, ratios[i])
        print(result)
    print(recommendations, ratios, nutrition)
     

if __name__ == "__main__":
    main()