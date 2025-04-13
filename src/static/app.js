$(document).ready(function () {
    console.log("Document ready");
    console.log("Clear history button exists: ", $("#clear-history").length);
    console.log("Clear chat button exists: ", $("#clear-chat").length);
    
    // Directly attach event to the clear history button
    document.getElementById("clear-history").addEventListener("click", function() {
        console.log("Clear history clicked via addEventListener");
        history = [];
        localStorage.setItem('recipeHistory', JSON.stringify([]));
        renderHistory();
        
        const alertHtml = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                推荐历史已清除
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        $("#history-container").closest(".card-body").prepend(alertHtml);
        
        setTimeout(() => {
            $(".alert").alert('close');
        }, 3000);
    });
    
    // Directly attach event to the clear chat button
    document.getElementById("clear-chat").addEventListener("click", function() {
        console.log("Clear chat clicked via addEventListener");
        chatHistory = [];
        localStorage.setItem('chatHistory', JSON.stringify([]));
        
        $("#chat-container").empty();
        showWelcomeMessage();
        
        const alertHtml = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                聊天记录已清除
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        $("#chat-container").closest(".card-body").prepend(alertHtml);
        
        setTimeout(() => {
            $(".alert").alert('close');
        }, 3000);
    });
    
    // Directly attach event to the submit rating button
    document.getElementById("submit-rating").addEventListener("click", function() {
        console.log("Submit rating clicked via addEventListener");
        const recipeName = $("#current-recipe").val();
        const historyIndex = parseInt($("#current-history-index").val());
        const rating = $("#recipe-rating").rateYo("rating");
        // 将5星制转换为10分制
        const score = rating * 2;
        
        console.log(`Submitting rating: ${score} for recipe: ${recipeName}, index: ${historyIndex}`);
        
        // 发送评分到后端
        $.ajax({
            url: "/update-pref",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                recipe: recipeName,
                rating: score  // 发送10分制的分数
            }),
            beforeSend: function(xhr) {
                console.log("Sending request to /update-pref");
                console.log("Request data:", JSON.stringify({
                    recipe: recipeName, 
                    rating: score
                }));
            },
            success: function(response) {
                console.log("Rating submission successful:", response);
                $("#ratingModal").modal("hide");
                
                // 显示成功消息
                const alertHtml = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        评分已提交！
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `;
                $(".card-body").prepend(alertHtml);
                
                // 3秒后自动移除提示
                setTimeout(() => {
                    $(".alert").alert('close');
                }, 3000);
                
                // 保存评分到历史记录
                if (!history[historyIndex].ratings) {
                    history[historyIndex].ratings = {};
                }
                history[historyIndex].ratings[recipeName] = score;
                saveToLocalStorage(); // 保存到 localStorage
                console.log("Rating saved to history and localStorage");
                
                // 更新历史记录中的星星显示
                try {
                    const selector = `.history-recipe-rating[data-recipe="${recipeName}"][data-history-index="${historyIndex}"]`;
                    console.log("Updating stars with selector:", selector);
                    const $stars = $(selector).find("i");
                    console.log("Found stars:", $stars.length);
                    $stars
                        .removeClass("far")
                        .addClass("fas")
                        .css("color", rating >= 3 ? "#28a745" : "#dc3545");
                    console.log("Stars updated successfully");
                } catch (e) {
                    console.error("Error updating stars:", e);
                }
                
                // 重新渲染历史记录以确保显示正确
                renderHistory();
            },
            error: function(xhr, status, error) {
                console.error("Rating submission failed:", {xhr, status, error});
                
                // 显示错误消息
                const alertHtml = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        评分提交失败，请稍后重试
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `;
                $(".card-body").prepend(alertHtml);
            }
        });
    });
    
    // 从 localStorage 加载数据
    let userData = JSON.parse(localStorage.getItem('userData')) || {
        height: 165.0,
        weight: 55.0,
        age: 25,
        gender: "female",
        pre_meal_glucose: 5.0,
        pre_meal_insulin: 0,
        activity_level: "moderately_active",
        TDEE: 1600
    };

    // 从 localStorage 加载历史记录
    let history = JSON.parse(localStorage.getItem('recipeHistory')) || [];
    let chatHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];

    // 欢迎消息模板
    const welcomeMessageTemplate = `
        <div class="chat-bubble bot-bubble">
            <div class="welcome-message">
                <h4>👋 你好！我是糖小智</h4>
                <p>我可以帮助你：</p>
                <ul>
                    <li>提供个性化的饮食建议</li>
                    <li>回答糖尿病相关问题</li>
                    <li>推荐适合的食谱</li>
                    <li>提供健康管理建议</li>
                </ul>
                <p>请告诉我你需要什么帮助？</p>
            </div>
        </div>
    `;

    // 显示欢迎消息函数
    function showWelcomeMessage() {
        const chatContainer = $("#chat-container");
        // 如果聊天容器为空或者只包含空白字符，添加欢迎消息
        if (!chatContainer.children().length) {
            chatContainer.html(welcomeMessageTemplate);
        }
    }

    // 立即渲染历史记录
    renderHistory();
    // 立即渲染聊天记录
    renderChatHistory();
    // 显示欢迎消息（如果没有聊天记录）
    showWelcomeMessage();

    // 显示/隐藏加载动画
    function toggleLoading(show) {
        if (show) {
            // 在聊天气泡中显示加载动画
            const loadingBubble = $(`
                <div class="chat-bubble bot-bubble">
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>思考中</span>
                    </div>
                </div>
            `);
            $("#chat-container").append(loadingBubble);
            $("#chat-container").scrollTop($("#chat-container")[0].scrollHeight);
        } else {
            // 移除最后一个聊天气泡（加载动画）
            $(".chat-bubble.bot-bubble").last().remove();
        }
    }

    // 保存数据到 localStorage
    function saveToLocalStorage() {
        localStorage.setItem('userData', JSON.stringify(userData));
        localStorage.setItem('recipeHistory', JSON.stringify(history));
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        console.log('数据已保存到 localStorage');
    }

    // 添加历史记录
    function addHistoryItem(data) {
        const now = new Date();
        const timeString = now.toLocaleString();
        
        const historyItem = {
            time: timeString,
            mealType: data.mealType,
            recipes: data.recommendations,
            stats: {
                healthScore: data.health_score,
                energy: data.energy,
                predictedGlucose: data.PBG,
                carb: data.carb,
                protein: data.protein,
                fat: data.fat,
                fiber: data.fiber
            },
            ratings: {}  // 添加空的评分对象，用于存储每个食谱的评分
        };
        
        history.unshift(historyItem); // 添加到开头
        renderHistory();
        saveToLocalStorage(); // 保存到 localStorage
    }

    // 渲染历史记录
    function renderHistory() {
        const container = $("#history-container");
        container.empty();
        
        // 显示空状态
        if (!history || history.length === 0) {
            container.html(`
                <div class="history-empty">
                    <i class="fas fa-history"></i>
                    <h4>暂无推荐记录</h4>
                    <p>与助手对话，获取个性化的食谱推荐。<br>您可以询问早餐、午餐或晚餐的食谱建议。</p>
                </div>
            `);
            return;
        }
        
        history.forEach((item, index) => {
            const historyItem = $(`
                <div class="history-item">
                    <div class="history-time">
                        <i class="far fa-clock me-1"></i>${item.time}
                    </div>
                    <div class="history-meal-type">
                        <i class="fas fa-utensils me-1"></i>${item.mealType}
                    </div>
                    <div class="history-recipes">
                        ${item.recipes.map(recipe => {
                            // 获取食谱评分（如果存在）
                            const rating = item.ratings && item.ratings[recipe];
                            const starClass = rating ? 'fas' : 'far';
                            const starColor = rating ? (rating >= 6 ? '#28a745' : '#dc3545') : '';
                            
                            return `
                            <div class="history-recipe">
                                <span class="history-recipe-name">
                                    <i class="fas fa-hamburger me-2"></i>${recipe}
                                </span>
                                <span class="history-recipe-rating" data-recipe="${recipe}" data-history-index="${index}" onclick="showRatingModal('${recipe}', ${index})">
                                    <i class="${starClass} fa-star" style="color: ${starColor}"></i>
                                    <i class="${starClass} fa-star" style="color: ${starColor}"></i>
                                    <i class="${starClass} fa-star" style="color: ${starColor}"></i>
                                    <i class="${starClass} fa-star" style="color: ${starColor}"></i>
                                    <i class="${starClass} fa-star" style="color: ${starColor}"></i>
                                </span>
                            </div>
                        `}).join('')}
                    </div>
                    <div class="history-stats">
                        <div><i class="fas fa-fire me-2"></i>总热量: ${item.stats.energy.toFixed(0)}kcal</div>
                        <div><i class="fas fa-tint me-2"></i>预测餐后2h血糖: ${item.stats.predictedGlucose.toFixed(2)}</div>
                        <div><i class="fas fa-bread-slice me-2"></i>碳水化合物: ${item.stats.carb.toFixed(1)}g</div>
                        <div><i class="fas fa-drumstick-bite me-2"></i>蛋白质: ${item.stats.protein.toFixed(1)}g</div>
                        <div><i class="fas fa-cheese me-2"></i>脂肪: ${item.stats.fat.toFixed(1)}g</div>
                        <div><i class="fas fa-seedling me-2"></i>膳食纤维: ${item.stats.fiber.toFixed(1)}g</div>
                    </div>
                </div>
            `);
            
            container.append(historyItem);
        });
        
        console.log("History rendered, attaching click events...");
    }

    // 渲染聊天记录
    function renderChatHistory() {
        const container = $("#chat-container");
        container.empty();
        
        chatHistory.forEach(item => {
            const bubbleClass = item.role === "user" ? "user-bubble" : "bot-bubble";
            const message = item.role === "bot" ? marked.parse(item.message) : item.message;
            const bubble = `<div class="chat-bubble ${bubbleClass}">${message}</div>`;
            container.append(bubble);
        });
        
        container.scrollTop(container[0].scrollHeight);
    }

    // 直接在全局作用域定义这个函数，以便能被内联的onclick调用
    window.showRatingModal = function(recipeName, historyIndex) {
        console.log(`showRatingModal called for ${recipeName}, index ${historyIndex}`);
        
        $("#current-recipe").val(recipeName);
        $("#current-history-index").val(historyIndex);
        
        // 如果已经有评分，则显示之前的评分
        const rating = history[historyIndex].ratings && history[historyIndex].ratings[recipeName];
        console.log("Current rating:", rating);
        $("#recipe-rating").rateYo("rating", rating ? rating/2 : 0);  // 将10分制转换回5星制
        
        console.log("Opening modal...");
        $("#ratingModal").modal("show");
    };
    
    // 初始化评分插件
    function initRating() {
        console.log("Initializing rating plugin...");
        try {
            $("#recipe-rating").rateYo({
                rating: 0,
                starWidth: "30px",
                fullStar: true,
                maxValue: 5,
                multiColor: {
                    "startColor": "#FF0000", // 红色开始
                    "endColor": "#00FF00"    // 绿色结束
                },
                onSet: function(rating) {
                    // 将5星制转换为10分制
                    const score = rating * 2;
                    console.log(`Rating set: ${rating} stars, Score: ${score} points`);
                }
            });
            console.log("Rating plugin initialized successfully");
        } catch (e) {
            console.error("Error initializing rating plugin:", e);
        }
    }
    
    // 确保在文档加载完成后初始化
    initRating();
    
    // 在模态框每次显示时重新初始化评分插件
    $("#ratingModal").on("shown.bs.modal", function() {
        console.log("Modal shown, reinitializing rating");
        try {
            const recipeName = $("#current-recipe").val();
            const historyIndex = parseInt($("#current-history-index").val());
            console.log(`Modal showing for ${recipeName}, index ${historyIndex}`);
            
            // 如果已经有评分，则显示之前的评分
            const rating = history[historyIndex].ratings && history[historyIndex].ratings[recipeName];
            $("#recipe-rating").rateYo("rating", rating ? rating/2 : 0);
        } catch (e) {
            console.error("Error setting rating in modal:", e);
        }
    });

    // 发送消息
    $("#send-message").on("click", function () {
        console.log("Send button clicked");
        const message = $("#chat-input").val();
        console.log("Message content:", message);
        if (!message) {
            console.log("Empty message, not sending");
            return;
        }
        
        // 检查用户是否已保存健康信息
        // 检查必要字段是否存在 - height, weight, age, gender, pre_meal_glucose
        if (!userData || !userData.height || !userData.weight || !userData.age || !userData.gender || !userData.pre_meal_glucose) {
            // 显示提示
            const alertHtml = `
                <div class="alert alert-warning alert-dismissible fade show" role="alert">
                    <strong>需要完善健康信息</strong> 
                    <p>为了给您提供个性化的饮食建议，我们需要了解您的基本健康数据。</p>
                    <p>即将为您跳转至健康信息页面，请填写相关信息。</p>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            $(".card-body").prepend(alertHtml);
            
            // 3秒后跳转到健康信息页面
            setTimeout(() => {
                window.location.href = "/data";
            }, 3000);
            
            return;
        }

        // 显示用户消息
        appendMessage("user", message);
        $("#chat-input").val("");

        // 显示加载动画
        toggleLoading(true);

        // 如果是食谱推荐请求，显示历史记录加载状态
        let isRecipeRequest = message.includes("推荐") && message.includes("食谱");
        console.log("Is recipe request:", isRecipeRequest);
        
        if (isRecipeRequest) {
            $("#history-container").html(`
                <div class="history-loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <div>正在生成推荐...</div>
                </div>
            `);
        }

        console.log("Sending data to backend:", {
            message: message,
            user_data: userData
        });

        // 发送到后端
        $.ajax({
            url: "/chat",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                message: message,
                user_data: userData
            }),
            success: function (response) {
                // 隐藏加载动画
                console.log("Server response:", response);
                toggleLoading(false);
                
                // 使用 marked 渲染 markdown
                const renderedMessage = marked.parse(response.message);
                appendMessage("bot", renderedMessage);
                
                // 如果是食谱推荐，添加到历史记录
                if (response.recipes) {
                    // 转换餐次类型为中文
                    const mealTypeMap = {
                        "breakfast": "早餐",
                        "lunch": "午餐",
                        "dinner": "晚餐"
                    };
                    
                    addHistoryItem({
                        mealType: mealTypeMap[response.mealType] || response.mealType,
                        recommendations: response.recipes,
                        health_score: response.health_score,
                        energy: response.energy,
                        PBG: response.PBG,
                        carb: response.carb,
                        protein: response.protein,
                        fat: response.fat,
                        fiber: response.fiber
                    });
                } else if (isRecipeRequest) {
                    // 如果不是食谱推荐但用户请求了食谱，显示空状态
                    renderHistory();
                }
            },
            error: function (xhr, status, error) {
                console.error("请求失败：", {xhr, status, error});
                // 隐藏加载动画
                toggleLoading(false);
                
                // 解析错误消息
                let errorMessage = "请求失败，请稍后重试。";
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.error) {
                        errorMessage = response.error;
                    }
                } catch (e) {
                    console.error("解析错误响应失败：", e);
                }
                
                appendMessage("bot", `<div class="error-message">${errorMessage}</div>`);
                // 恢复历史记录显示
                renderHistory();
            }
        });
    });

    // 添加消息到聊天框
    function appendMessage(role, message) {
        const bubbleClass = role === "user" ? "user-bubble" : "bot-bubble";
        const bubble = `<div class="chat-bubble ${bubbleClass}">${message}</div>`;
        $("#chat-container").append(bubble);
        $("#chat-container").scrollTop($("#chat-container")[0].scrollHeight);
        
        // 添加到聊天历史
        chatHistory.push({ role, message });
        saveToLocalStorage(); // 保存到 localStorage
    }

    // 按回车发送消息
    $("#chat-input").on("keypress", function (e) {
        if (e.which === 13) {
            $("#send-message").click();
        }
    });

    // 输入框获得焦点时显示提示
    $("#chat-input").on("focus", function() {
        $(this).attr("placeholder", "例如：请推荐一些适合糖尿病患者的早餐食谱");
    }).on("blur", function() {
        $(this).attr("placeholder", "请输入您的问题...");
    });

    // 添加输入建议
    const suggestions = [
        "请推荐一些适合糖尿病患者的早餐食谱",
        "糖尿病患者可以吃水果吗？",
        "如何控制血糖？",
        "推荐一些低糖的零食",
        "运动对糖尿病有什么好处？"
    ];

    let currentSuggestion = 0;
    setInterval(function() {
        $("#chat-input").attr("placeholder", suggestions[currentSuggestion]);
        currentSuggestion = (currentSuggestion + 1) % suggestions.length;
    }, 3000);
});