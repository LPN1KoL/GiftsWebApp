const tg = window.Telegram?.WebApp;
tg.expand();


if (!tg.initDataUnsafe?.user?.id) {
    window.location.href = "/404";
}

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
                                    <img class="starr" src="data:image/svg+xml,%3csvg%20viewBox='0%200%2014%2015'%20fill='%23FFCA5A'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20fill-rule='evenodd'%20clip-rule='evenodd'%20d='M6.63869%2012.1902L3.50621%2014.1092C3.18049%2014.3087%202.75468%2014.2064%202.55515%2013.8807C2.45769%2013.7216%202.42864%2013.5299%202.47457%2013.3491L2.95948%2011.4405C3.13452%2010.7515%203.60599%2010.1756%204.24682%209.86791L7.6642%208.22716C7.82352%208.15067%207.89067%207.95951%207.81418%207.80019C7.75223%207.67116%207.61214%207.59896%207.47111%207.62338L3.66713%208.28194C2.89387%208.41581%202.1009%208.20228%201.49941%207.69823L0.297703%206.69116C0.00493565%206.44581%20-0.0335059%206.00958%200.211842%205.71682C0.33117%205.57442%200.502766%205.48602%200.687982%205.47153L4.35956%205.18419C4.61895%205.16389%204.845%204.99974%204.94458%204.75937L6.36101%201.3402C6.5072%200.987302%206.91179%200.819734%207.26469%200.965925C7.43413%201.03612%207.56876%201.17075%207.63896%201.3402L9.05539%204.75937C9.15496%204.99974%209.38101%205.16389%209.6404%205.18419L13.3322%205.47311C13.713%205.50291%2013.9975%205.83578%2013.9677%206.2166C13.9534%206.39979%2013.8667%206.56975%2013.7269%206.68896L10.9114%209.08928C10.7131%209.25826%2010.6267%209.52425%2010.6876%209.77748L11.5532%2013.3733C11.6426%2013.7447%2011.414%2014.1182%2011.0427%2014.2076C10.8642%2014.2506%2010.676%2014.2208%2010.5195%2014.1249L7.36128%2012.1902C7.13956%2012.0544%206.8604%2012.0544%206.63869%2012.1902Z'%20fill='%23FFCA5A'%3e%3c/path%3e%3c/svg%3e">
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
        
        
        if (result.subscribed) {
            document.getElementById("quest-subscribe").style.display = "none";
        }

        if (result.today_opened_cases >= 10) {
            document.getElementById("quest-open-case-10").style.display = "none";
        } else {
            document.getElementById("quest-open-case-10").querySelector(".progress h2").textContent = `${result.today_opened_cases * 10}%`;
            document.getElementById("quest-open-case-10").querySelector(".bar").classList.add(`prog${result.today_opened_cases * 10}`);
        }

        if (result.today_opened_cases >= 25) {
            document.getElementById("quest-open-case-25").style.display = "none";
        } else {
            document.getElementById("quest-open-case-25").querySelector(".progress h2").textContent = `${result.today_opened_cases * 4}%`;
            document.getElementById("quest-open-case-25").querySelector(".bar").classList.add(`prog${result.today_opened_cases * 4}`);
        }

        if (result.everyday_visits >= 25) {
            document.getElementById("quest-login-25").style.display = "none";
        } else {
            document.getElementById("quest-login-25").querySelector(".progress h2").textContent = `${result.everyday_visits * 4}%`;
            document.getElementById("quest-login-25").querySelector(".bar").classList.add(`prog${result.everyday_visits * 4}`);
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
    const btn = document.getElementById('sell_gift');
    try {
        btn.setAttribute('disabled', '');
        btn.innerText = 'Подождите...';
        btn.style.backgroundColor = '#227734ff';
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
        btn.style.backgroundColor = '#4ABD33';
    }
    
}

function cardClick(gift_id){
    card = document.getElementById('card-' + gift_id) // Можно получить цену, картинку, подставить в всплывающее окно
    image = card.querySelector('.gimg').src
    price = card.querySelector('.ct h2').textContent
    modal = document.querySelector('.modal')
    modal.querySelector('.img img').src = image
    modal.querySelector('h2').textContent = price
    document.getElementById("get_gift").onclick = () => get_gift(gift_id);
    document.getElementById("sell_gift").onclick = () => sell_gift(gift_id);
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