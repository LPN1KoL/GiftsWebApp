const tg = window.Telegram?.WebApp;
tg.expand();

document.addEventListener('DOMContentLoaded', () => {
	const user_id = tg.initDataUnsafe?.user?.id;


    const plusButton = document.getElementById('main_button');

    async function sendApiRequest(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const json = await response.json();
            if (!response.ok) {
                throw new Error(json.error || "Unknown error");
            }
            return json;
        } catch (error) {
            console.error("Ошибка запроса:", error);
            throw error;
        }
    }



async function updateProfile() {
    try {
        const result = await sendApiRequest('/api/get_profile', { user_id });
        
        // Обновляем баланс
        const balanceElement = document.getElementById('balance_display');
        if (balanceElement) {
            balanceElement.textContent = result.balance.toLocaleString();
        }

        // Обновляем ник
        const usernameElement = document.querySelector('.profile h1');
        if (usernameElement) {
            usernameElement.textContent = '@' + tg.initDataUnsafe.user.username;
        }

        // Обновляем аватар
        const avatarElement = document.querySelector('.user-pic img');
        if (avatarElement) {
            avatarElement.src = tg.initDataUnsafe.user.photo_url;
        }

        // Отображаем подарки
        const cardList = document.querySelector('.card-list');
        if (cardList) {
            cardList.innerHTML = ""; // очистим старые

            if (result.gifts && result.gifts.length > 0) {
                result.gifts.forEach(gift => {
                    const card = document.createElement('div');
                    card.classList.add('card');

                    card.innerHTML = `
                        <div class="gift-img">
                            <img class="gimg" src="${gift.img}" alt="${gift.name}">
                        </div>
                        <h2 class="name">${gift.name}</h2>
                        <div class="price">
                            <div class="pc">
                                <div class="starss">
                                    <img class="starr" src="data:image/svg+xml,%3Csvg ... %3C/svg%3E">
                                </div>
                                <div class="ct">
                                    <h2>${gift.price.toLocaleString()}</h2>
                                </div>
                            </div>
                        </div>
                    `;
                    cardList.appendChild(card);
                });
            } else {
                document.getElementById("wrap").innerHTML = ""
            }
        }

    } catch (err) {
        console.error("Ошибка при получении профиля:", err);

        const balanceElement = document.getElementById('balance_display');
        if (balanceElement) {
            balanceElement.textContent = "Ошибка";
        }
    }
}


    updateProfile();
});

function cardClick(gift_id){
    card = document.getElementById('card ' + gift_id) // Можно получить цену, картинку, подставить в всплывающее окно
    document.querySelector('.modal').classList.add('active');
}

function plus_func(){
    let tg = window.Telegram?.WebApp;
    let user_id = tg.initDataUnsafe?.user?.id
    if (!user_id) {
        alert("Ошибка: Не удалось определить Telegram ID");
        return;
    }

    try {
        tg.sendData(JSON.stringify({foo: "donate"}));
        tg.close();
    } catch (err) {
        alert("Ошибка при отправке: " + err.message);
    }
}