window.Telegram?.WebApp?.expand();

let selectedCase = null;
const SLIDER_LENGTH = 32;
const WIN_INDEX = 29; // индекс выигрышной карточки
const CARD_WIDTH = 35; // vw
const CARD_MARGIN = 4;
const CARD_TOTAL = CARD_WIDTH + CARD_MARGIN; // 39vw
const params = new URLSearchParams(window.location.search);

caseId = params.get('case_id');
if (!caseId) {
    if (!localStorage.getItem('case_id')) {
        caseId = container.dataset.caseId;
        localStorage.setItem('case_id', caseId);
    }
} else {
    localStorage.setItem('case_id', caseId);
}

if (localStorage.getItem('case_id')) {
    caseId = localStorage.getItem('case_id');
    document.getElementById("main_link").href = "/main?case_id=" + caseId;
}

// Получаем user_id из Telegram WebApp или используем тестовый
let user_id = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;



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

async function updateBalance() {
    try {
        const result = await sendApiRequest('/api/get_balance', { user_id });
        const balanceElement = document.getElementById('balance_display');
        if (balanceElement) {
            balanceElement.textContent = result.balance.toLocaleString();
        }
        return result.balance;
    } catch (err) {
        console.error("Ошибка при получении баланса:", err);
        const balanceElement = document.getElementById('balance_display');
        if (balanceElement) {
            balanceElement.textContent = "Ошибка";
        }
        return 0;
    }
}

function getRandomGifts(gifts, count, wonGift = null, winIndex = null) {
    let arr = [];
    for (let i = 0; i < count; i++) {
        arr.push(selectGiftByChance(gifts));
    }
    if (wonGift && winIndex !== null) arr[winIndex] = wonGift;
    return arr;
}

function selectGiftByChance(giftsList) {
    const rnd = Math.random();
    let cumulative = 0;
    let selectedGift = null;

    for (const gift of giftsList) {
        const chance = gift.chance;
        if (chance == null) continue;
        cumulative += chance;
        if (rnd <= cumulative) {
            selectedGift = gift;
            break;
        }
    }

    if (!selectedGift) {
        selectedGift = giftsList[giftsList.length - 1];
    }
    return selectedGift;
}

function renderSlider(wonGift = null) {
    const slider = document.getElementById('slide');
    slider.innerHTML = '';
    const gifts = JSON.parse(document.getElementById('data-block').dataset.randomGifts).random_gifts;
    for(let i = 0; i < gifts.length; i++) {

        // Выбираем подарок по шансам
        if (wonGift && i==WIN_INDEX) {
            const gift = wonGift;
            const card = document.createElement('div');
            card.className = 'card';
            card.style.width = CARD_WIDTH + 'vw';
            card.style.display = 'inline-block';
            card.style.margin = '1vh 2vw';
            if (gift) {
                card.innerHTML = `
                    <div class="gift-img">
                        <img class="gimg" src="${gift.image}" alt="Подарок">
                    </div>
                    <h2 class="name">${gift.name}</h2>
                    <div class="price">
                        <div class="pc">
                            <div class="starss">
                                <img class="starr" src="data:image/svg+xml,%3csvg%20viewBox='0%200%2014%2015'%20fill='%23FFCA5A'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20fill-rule='evenodd'%20clip-rule='evenodd'%20d='M6.63869%2012.1902L3.50621%2014.1092C3.18049%2014.3087%202.75468%2014.2064%202.55515%2013.8807C2.45769%2013.7216%202.42864%2013.5299%202.47457%2013.3491L2.95948%2011.4405C3.13452%2010.7515%203.60599%2010.1756%204.24682%209.86791L7.6642%208.22716C7.82352%208.15067%207.89067%207.95951%207.81418%207.80019C7.75223%207.67116%207.61214%207.59896%207.47111%207.62338L3.66713%208.28194C2.89387%208.41581%202.1009%208.20228%201.49941%207.69823L0.297703%206.69116C0.00493565%206.44581%20-0.0335059%206.00958%200.211842%205.71682C0.33117%205.57442%200.502766%205.48602%200.687982%205.47153L4.35956%205.18419C4.61895%205.16389%204.845%204.99974%204.94458%204.75937L6.36101%201.3402C6.5072%200.987302%206.91179%200.819734%207.26469%200.965925C7.43413%201.03612%207.56876%201.17075%207.63896%201.3402L9.05539%204.75937C9.15496%204.99974%209.38101%205.16389%209.6404%205.18419L13.3322%205.47311C13.713%205.50291%2013.9975%205.83578%2013.9677%206.2166C13.9534%206.39979%2013.8667%206.56975%2013.7269%206.68896L10.9114%209.08928C10.7131%209.25826%2010.6267%209.52425%2010.6876%209.77748L11.5532%2013.3733C11.6426%2013.7447%2011.414%2014.1182%2011.0427%2014.2076C10.8642%2014.2506%2010.676%2014.2208%2010.5195%2014.1249L7.36128%2012.1902C7.13956%2012.0544%206.8604%2012.0544%206.63869%2012.1902Z'%20fill='%23FFCA5A'%3e%3c/path%3e%3c/svg%3e" alt="">
                            </div>
                            <div class="ct">
                                <h2>${gift.price}</h2>
                            </div>
                        </div>
                    </div>
                `;
            }
            slider.appendChild(card);
        };
    
        const gift = gifts[i];
        const card = document.createElement('div');
        card.className = 'card';
        card.style.width = CARD_WIDTH + 'vw';
        card.style.display = 'inline-block';
        card.style.margin = '1vh 2vw';
        if (gift) {
            card.innerHTML = `
                <div class="gift-img">
                    <img class="gimg" src="${gift.image}" alt="Подарок">
                </div>
                <h2 class="name">${gift.name}</h2>
                <div class="price">
                    <div class="pc">
                        <div class="starss">
                            <img class="starr" src="data:image/svg+xml,%3csvg%20viewBox='0%200%2014%2015'%20fill='%23FFCA5A'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20fill-rule='evenodd'%20clip-rule='evenodd'%20d='M6.63869%2012.1902L3.50621%2014.1092C3.18049%2014.3087%202.75468%2014.2064%202.55515%2013.8807C2.45769%2013.7216%202.42864%2013.5299%202.47457%2013.3491L2.95948%2011.4405C3.13452%2010.7515%203.60599%2010.1756%204.24682%209.86791L7.6642%208.22716C7.82352%208.15067%207.89067%207.95951%207.81418%207.80019C7.75223%207.67116%207.61214%207.59896%207.47111%207.62338L3.66713%208.28194C2.89387%208.41581%202.1009%208.20228%201.49941%207.69823L0.297703%206.69116C0.00493565%206.44581%20-0.0335059%206.00958%200.211842%205.71682C0.33117%205.57442%200.502766%205.48602%200.687982%205.47153L4.35956%205.18419C4.61895%205.16389%204.845%204.99974%204.94458%204.75937L6.36101%201.3402C6.5072%200.987302%206.91179%200.819734%207.26469%200.965925C7.43413%201.03612%207.56876%201.17075%207.63896%201.3402L9.05539%204.75937C9.15496%204.99974%209.38101%205.16389%209.6404%205.18419L13.3322%205.47311C13.713%205.50291%2013.9975%205.83578%2013.9677%206.2166C13.9534%206.39979%2013.8667%206.56975%2013.7269%206.68896L10.9114%209.08928C10.7131%209.25826%2010.6267%209.52425%2010.6876%209.77748L11.5532%2013.3733C11.6426%2013.7447%2011.414%2014.1182%2011.0427%2014.2076C10.8642%2014.2506%2010.676%2014.2208%2010.5195%2014.1249L7.36128%2012.1902C7.13956%2012.0544%206.8604%2012.0544%206.63869%2012.1902Z'%20fill='%23FFCA5A'%3e%3c/path%3e%3c/svg%3e" alt="">
                        </div>
                        <div class="ct">
                            <h2>${gift.price}</h2>
                        </div>
                    </div>
                </div>
            `;
        }
    
    slider.appendChild(card);    
    slider.style.width = (CARD_TOTAL * gifts.length) + 'vw';
    slider.style.transition = 'none';
    slider.style.transform = 'translateX(0vw)';
    }
}

async function loadCaseData() {
    try {
        const response = await fetch('/data/cases.json');
        const cases = await response.json();
        selectedCase = cases.find(c => c.id === caseId);

        if (!selectedCase) {
            alert('Кейс не найден');
            return;
        }

        document.getElementById('case_name').textContent = selectedCase.name;

        // Список подарков
        const giftsContainer = document.querySelector('.list-items');
        giftsContainer.innerHTML = '';
        selectedCase.gifts.forEach(gift => {
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = `
                <div class="gift-img">
                    <img class="gimg" src="${gift.img}" alt="Подарок">
                </div>
                <h2 class="name">${gift.name}</h2>
                <div class="price">
                    <div class="pc">
                        <div class="starss">
                            <img class="starr" src="data:image/svg+xml,%3csvg%20viewBox='0%200%2014%2015'%20fill='%23FFCA5A'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20fill-rule='evenodd'%20clip-rule='evenodd'%20d='M6.63869%2012.1902L3.50621%2014.1092C3.18049%2014.3087%202.75468%2014.2064%202.55515%2013.8807C2.45769%2013.7216%202.42864%2013.5299%202.47457%2013.3491L2.95948%2011.4405C3.13452%2010.7515%203.60599%2010.1756%204.24682%209.86791L7.6642%208.22716C7.82352%208.15067%207.89067%207.95951%207.81418%207.80019C7.75223%207.67116%207.61214%207.59896%207.47111%207.62338L3.66713%208.28194C2.89387%208.41581%202.1009%208.20228%201.49941%207.69823L0.297703%206.69116C0.00493565%206.44581%20-0.0335059%206.00958%200.211842%205.71682C0.33117%205.57442%200.502766%205.48602%200.687982%205.47153L4.35956%205.18419C4.61895%205.16389%204.845%204.99974%204.94458%204.75937L6.36101%201.3402C6.5072%200.987302%206.91179%200.819734%207.26469%200.965925C7.43413%201.03612%207.56876%201.17075%207.63896%201.3402L9.05539%204.75937C9.15496%204.99974%209.38101%205.16389%209.6404%205.18419L13.3322%205.47311C13.713%205.50291%2013.9975%205.83578%2013.9677%206.2166C13.9534%206.39979%2013.8667%206.56975%2013.7269%206.68896L10.9114%209.08928C10.7131%209.25826%2010.6267%209.52425%2010.6876%209.77748L11.5532%2013.3733C11.6426%2013.7447%2011.414%2014.1182%2011.0427%2014.2076C10.8642%2014.2506%2010.676%2014.2208%2010.5195%2014.1249L7.36128%2012.1902C7.13956%2012.0544%206.8604%2012.0544%206.63869%2012.1902Z'%20fill='%23FFCA5A'%3e%3c/path%3e%3c/svg%3e" alt="">
                        </div>
                        <div class="ct">
                            <h2>${gift.price}</h2>
                        </div>
                    </div>
                </div>
            `;
            giftsContainer.appendChild(card);
        });

        // Слайдер: случайные подарки
        const randomGifts = getRandomGifts(selectedCase.gifts, SLIDER_LENGTH);
        renderSlider(randomGifts);
        
        // Обновляем баланс при загрузке страницы
        await updateBalance();
    } catch (e) {
        console.error('Ошибка загрузки данных кейса:', e);
    }
}

async function open_case() {

    const btn = document.getElementById('open_case');
    btn.setAttribute('disabled', '');
    btn.innerText = 'Открываем...';
    btn.style.backgroundColor = '#255ea0';


    try {
        tg = window.Telegram?.WebApp;
        // Отправляем запрос на открытие кейса
        const result = await sendApiRequest('/api/open_case', {
            init_data: tg.initData,
            case_id: document.getElementById('data-block').dataset.caseId
        });
        console.log(result);

        if (result) {
        
            const wonGift = result.gift;

            renderSlider(wonGift);

            const slider = document.getElementById('slide');
            // Анимация: transition к выигрышу
            slider.style.transition = 'transform 3s cubic-bezier(0.33,1,0.68,1)';
            // Добавляем случайный разброс внутри одной карточки
            const randomOffset = Math.random() * CARD_WIDTH - CARD_WIDTH / 2; // от -CARD_WIDTH/2 до +CARD_WIDTH/2
            const targetX = -((WIN_INDEX - 1) * CARD_TOTAL + randomOffset);
            slider.style.transform = `translateX(${targetX}vw)`;

            await sleep(3100);

            if (wonGift) {
                showWinModal(wonGift);
            } else {
                alert('Подарок не найден');
            }
            renderSlider();
        }
        else {
            alert(result.response);
        }
        
    } catch (error) {
        alert('Ошибка при открытии кейса: ' + error.message);
    }

    btn.removeAttribute('disabled');
    btn.innerText = 'Открыть';
    btn.style.backgroundColor = '#3281dc';
}

function showWinModal(gift) {
    const modal = document.querySelector('.modal');
    const imgEl = modal.querySelector('.img img');
    const countEl = modal.querySelector('.cnt');
    const caseNameEl = document.getElementById('case_name');

    if (gift) {
        imgEl.src = gift.img;               // картинка подарка
        countEl.textContent = gift.price || ""; // цена/очки (если есть)
        caseNameEl.textContent = gift.name || "Ваш подарок";
    }

    modal.classList.add('active');
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


//document.addEventListener('DOMContentLoaded', loadCaseData);


