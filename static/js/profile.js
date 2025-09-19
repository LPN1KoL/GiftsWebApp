const tg = window.Telegram?.WebApp;
tg.expand();

function plus_func(){
    if (!tg) {
        alert("WebApp не инициализирован");
        return;
    }

    const user_id = tg.initDataUnsafe?.user?.id;
    if (!user_id) {
        alert("Ошибка: Не удалось определить Telegram ID");
        return;
    }

    try {
        tg.sendData(JSON.stringify({action: "donate",}));
        tg.close();
    } catch (err) {
        alert("Ошибка при отправке: " + err.message);
    }
}

async function sendApiRequest(endpoint, data) {
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
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function updateProfile() {
    try {
        const user_id = tg.initDataUnsafe?.user?.id;
        if (!user_id) {
            alert("Ошибка: Не удалось определить Telegram ID");
            return;
        }
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
                    card.onclick = () => cardClick(gift.id);
                    card.id = 'card-' + gift.id;

                    card.innerHTML = `
                        <div class="gift-img">
                            <img class="gimg" src="${gift.image}" alt="${gift.name}">
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
        document.querySelector('.loading-wrapper').style.display = 'none';
        document.querySelector('.main').style.display = 'block';

    } catch (err) {
        console.error("Ошибка при получении профиля:", err);

        const balanceElement = document.getElementById('balance_display');
        if (balanceElement) {
            balanceElement.textContent = "Ошибка";
        }
    }
}


// Загружаем профиль при загрузке страницы
if (tg) {
    updateProfile();
} else {
    alert("WebApp не инициализирован");
}

//Обновляем ссылку на кейс
if (localStorage.getItem('case_id')) {
    caseId = localStorage.getItem('case_id');
    document.getElementById('main_link').href = `/main?case_id=${caseId}`;
}

async function sell_gift(gift_id){
    const btn = document.getElementById('sell_btn');
    try {
        btn.setAttribute('disabled', '');
        btn.innerText = 'Подождите...';
        btn.style.backgroundColor = '#255ea0';
        const tg = window.Telegram?.WebApp;
        const result = await sendApiRequest('/api/sell_gift', { initData: tg.initData, gift_id: gift_id });
        if (result && result.success) {
            window.location.reload();
            return;
        } else {
            alert('Ошибка при продаже подарка');
            console.error("Ошибка при продаже подарка:", result);
        }

    } catch (err) {
        console.error("Ошибка при продаже подарка:", err);
        alert('Ошибка при продаже подарка');
    } finally {
        document.querySelector('.modal').classList.remove('active');
        btn.removeAttribute('disabled');
        btn.innerText = 'Продать';
        btn.style.backgroundColor = '#3281dc';
    }
    
}

function cardClick(gift_id){
    card = document.getElementById('card-' + gift_id) // Можно получить цену, картинку, подставить в всплывающее окно
    image = card.querySelector('.gimg').src
    price = card.querySelector('.ct h2').textContent
    modal = document.querySelector('.modal')
    modal.querySelector('.img img').src = image
    modal.querySelector('.cnt h2').textContent = price
    modal.getElementById("get_gift").onclick = () => get_gift(gift.id);
    modal.getElementById("sell_gift").onclick = () => sell_gift(gift.id);
    modal.classList.add('active');
}

async function get_gift(gift_id){
    const btn = document.getElementById('get_gift');
    btn.setAttribute('disabled', '');
    btn.innerText = 'Подождите...';
    btn.style.backgroundColor = '#255ea0';
    const result = await sendApiRequest('/api/get_gift', { gift_id: gift_id, initData: tg.initData });
    
    if (result && result.success) {
        alert("Запрос на вывод подарка отправлен!");
        window.location.reload();
    } else {
        alert('Ошибка при получении подарка');
        console.error("Ошибка при получении подарка:", result);
    }

    document.querySelector('.modal').classList.remove('active');
    btn.removeAttribute('disabled');
    btn.innerText = 'Получить';
    btn.style.backgroundColor = '#3281dc';
}