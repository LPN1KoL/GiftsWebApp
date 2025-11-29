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

let user_id = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
if (!user_id) {
    window.location.href = "/404";
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


function randomizeSlider() {
    let random_gifts = JSON.parse(document.getElementById('data-block').dataset.randomGifts).random_gifts;
    random_gifts = random_gifts.sort(() => Math.random() - 0.5);
    document.getElementById('data-block').dataset.randomGifts = JSON.stringify({ random_gifts: random_gifts });
}


async function open_case() {

    const btn = document.getElementById('open_case');
    btn.setAttribute('disabled', '');
    btn.innerText = 'Открываем...';
    btn.style.backgroundColor = '#255ea0';
    const demo = document.getElementById('demo').checked;


    try {
        tg = window.Telegram?.WebApp;
        const result = await sendApiRequest('/api/open_case', {
            init_data: tg.initData,
            case_id: document.getElementById('data-block').dataset.caseId,
            demo: demo
        });

        if (!result.error) {
        
            const wonGift = result.gift;

            renderSlider(wonGift);

            const slider = document.getElementById('slide');
            slider.style.transition = 'transform 3s cubic-bezier(0.33,1,0.68,1)';
            let randomOffset = 0;
            if (Math.random() < 0.5) {
                randomOffset = Math.random() * (CARD_WIDTH / 2);
            } else {
                randomOffset = Math.random() * (-1) * (CARD_WIDTH / 2);
            }
            const targetX = -(((WIN_INDEX - 1) * CARD_TOTAL) + randomOffset);
            slider.style.transform = `translateX(${targetX}vw)`;

            await sleep(3200);

            if (wonGift) {
                showWinModal(wonGift, demo);
            } else {
                alert('Подарок не найден');
            }
            await sleep(300);
            randomizeSlider();
            renderSlider();
        }
        else {
            console.error(result)
            alert(result.error);
        }
        
    } catch (error) {
        console.error(error)
        alert("Ошибка при открытии кейса");
    }

    btn.removeAttribute('disabled');
    btn.innerText = 'Открыть';
    btn.style.backgroundColor = '#3281dc';
}

function showWinModal(gift, demo) {

    const modal = document.getElementById("modal");
    document.getElementById('sell_btn').style.display = "block";
    modal.querySelector('.holder').innerHTML = `
            <div class="stars">
                <img src="data:image/svg+xml,%3csvg%20viewBox='0%200%2014%2015'%20fill='%23FFCA5A'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20fill-rule='evenodd'%20clip-rule='evenodd'%20d='M6.63869%2012.1902L3.50621%2014.1092C3.18049%2014.3087%202.75468%2014.2064%202.55515%2013.8807C2.45769%2013.7216%202.42864%2013.5299%202.47457%2013.3491L2.95948%2011.4405C3.13452%2010.7515%203.60599%2010.1756%204.24682%209.86791L7.6642%208.22716C7.82352%208.15067%207.89067%207.95951%207.81418%207.80019C7.75223%207.67116%207.61214%207.59896%207.47111%207.62338L3.66713%208.28194C2.89387%208.41581%202.1009%208.20228%201.49941%207.69823L0.297703%206.69116C0.00493565%206.44581%20-0.0335059%206.00958%200.211842%205.71682C0.33117%205.57442%200.502766%205.48602%200.687982%205.47153L4.35956%205.18419C4.61895%205.16389%204.845%204.99974%204.94458%204.75937L6.36101%201.3402C6.5072%200.987302%206.91179%200.819734%207.26469%200.965925C7.43413%201.03612%207.56876%201.17075%207.63896%201.3402L9.05539%204.75937C9.15496%204.99974%209.38101%205.16389%209.6404%205.18419L13.3322%205.47311C13.713%205.50291%2013.9975%205.83578%2013.9677%206.2166C13.9534%206.39979%2013.8667%206.56975%2013.7269%206.68896L10.9114%209.08928C10.7131%209.25826%2010.6267%209.52425%2010.6876%209.77748L11.5532%2013.3733C11.6426%2013.7447%2011.414%2014.1182%2011.0427%2014.2076C10.8642%2014.2506%2010.676%2014.2208%2010.5195%2014.1249L7.36128%2012.1902C7.13956%2012.0544%206.8604%2012.0544%206.63869%2012.1902Z'%20fill='%23FFCA5A'%3e%3c/path%3e%3c/svg%3e" alt="">
            </div>
            <div class="count">
                <h2 class="cnt"></h2>
            </div>
    `;

    if (gift) {

        if (!demo) {
            if (gift.price){
                modal.querySelector('.cnt').textContent = gift.price;
                document.getElementById('sell_btn').onclick = () => sell_gift(gift.id);
                modal.querySelector('.img img').src = gift.image;
            } else {
                modal.querySelector('.img img').src = '/media/failed.png';
                modal.querySelector('.holder').innerHTML = '<h2 style="color: white;" class="cnt">Повезёт в другой раз</h2>';
                document.getElementById('sell_btn').style.display = "none";
            }
        } else {
            modal.querySelector('.img img').src = gift.image;
            modal.querySelector('.holder').innerHTML = '<h2 style="color: white;" class="cnt">Режим тестирования</h2>';
            document.getElementById('sell_btn').style.display = "none";
        }

        modal.classList.add('active');
    }

}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
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

async function updateUserLastVisit() {
    await sendApiRequest('/api/update_last_visit', { init_data: window.Telegram?.WebApp?.initData });
}

updateUserLastVisit();