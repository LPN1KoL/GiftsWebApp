let selectedCase = null;
const SLIDER_LENGTH = 32;
const WIN_INDEX = 29; // индекс выигрышной карточки
const CARD_WIDTH = 35; // vw
const CARD_MARGIN = 4;
const CARD_TOTAL = CARD_WIDTH + CARD_MARGIN; // 39vw

// Получаем user_id из Telegram WebApp или используем тестовый
let user_id = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || "849307631";

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
    while (arr.length < count) arr = arr.concat(gifts.slice());
    arr = arr.slice(0, count);
    if (wonGift && winIndex !== null) arr[winIndex] = wonGift;
    return arr;
}

function renderSlider(giftsArr, highlightIndex = null) {
    const slider = document.getElementById('slide');
    slider.innerHTML = '';
    giftsArr.forEach((gift, idx) => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.width = CARD_WIDTH + 'vw';
        card.style.display = 'inline-block';
        card.style.margin = '1vh 2vw';
        if (gift) {
            card.innerHTML = `
                <img src="${gift.img}" alt="Подарок">
            `;
        }
        slider.appendChild(card);
    });
    slider.style.width = (CARD_TOTAL * giftsArr.length) + 'vw';
    slider.style.transition = 'none';
    slider.style.transform = 'translateX(0vw)';
}

async function loadCaseData() {
    const params = new URLSearchParams(window.location.search);
    caseId = params.get('id');
    if (!caseId) {
        caseId = "basic1"
    }

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
                <img src="${gift.img}" alt="Подарок"">
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

    if (!selectedCase) {
        alert('Данные кейса не загружены');
        btn.removeAttribute('disabled');
        btn.innerText = 'Открыть';
        btn.style.backgroundColor = '#3281dc';
        return;
    }

    // Проверяем баланс перед открытием
    const balance = await updateBalance();
    if (balance <= 0) {
        alert('Недостаточно средств для открытия кейса');
        btn.removeAttribute('disabled');
        btn.innerText = 'Открыть';
        btn.style.backgroundColor = '#3281dc';
        return;
    }

    try {
        // Отправляем запрос на открытие кейса
        const result = await sendApiRequest('/api/open_case', {
            user_id: user_id,
            case_id: selectedCase.id
        });
        
        const wonGift = result.gift;
        
        // Массив для слайдера, на WIN_INDEX выигрыш
        const sliderGifts = getRandomGifts(selectedCase.gifts, SLIDER_LENGTH, wonGift, WIN_INDEX);
        renderSlider(sliderGifts);

        const slider = document.getElementById('slide');
        await sleep(400);

        // Анимация: transition к выигрышу
        slider.style.transition = 'transform 3s cubic-bezier(0.33,1,0.68,1)';
        const targetX = -((WIN_INDEX - 1) * CARD_TOTAL);
        slider.style.transform = `translateX(${targetX}vw)`;

        await sleep(3100);
        slider.style.transition = 'none';
        renderSlider(sliderGifts, WIN_INDEX);
        slider.style.transform = `translateX(${targetX}vw)`;

        if (wonGift) {
            alert(`Поздравляем! Вы получили подарок!\n\nСсылка: ${wonGift.link}`);
        } else {
            alert('подарок не найден :');
        }
        
        // Обновляем баланс после открытия кейса
        await updateBalance();
    } catch (error) {
        alert('Ошибка при открытии кейса: ' + error.message);
    }

    btn.removeAttribute('disabled');
    btn.innerText = 'Открыть';
    btn.style.backgroundColor = '#3281dc';
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Обработчик для кнопки "Пополнить баланс"
document.getElementById('main_button')?.addEventListener('click', async () => {
    if (!user_id) {
        alert("Ошибка: Не удалось определить Telegram ID");
        return;
    }

    try {
        const result = await sendApiRequest('/api/plus', { user_id });
        alert("Запрос успешно отправлен!");
        await updateBalance();
    } catch (err) {
        alert("Ошибка при отправке: " + err.message);
    }
});

document.addEventListener('DOMContentLoaded', loadCaseData);