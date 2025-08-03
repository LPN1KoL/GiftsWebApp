let selectedCase = null;
const SLIDER_LENGTH = 32;
const WIN_INDEX = 29; // индекс выигрышной карточки
const CARD_WIDTH = 35; // vw
const CARD_MARGIN = 4;
const CARD_TOTAL = CARD_WIDTH + CARD_MARGIN; // 39vw

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
  const caseId = params.get('id');
  if (!caseId) {
    alert('Кейс не выбран');
    return;
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

  // Выбор подарка
  const gifts = selectedCase.gifts;
  let rand = Math.random();
  let sum = 0;
  let wonGift = null;
  for (let gift of gifts) {
    sum += gift.chance;
    if (rand <= sum) {
      wonGift = gift;
      break;
    }
  }
  if (!wonGift) wonGift = gifts[gifts.length - 1];

  // Массив для слайдера, на WIN_INDEX выигрыш
  const sliderGifts = getRandomGifts(gifts, SLIDER_LENGTH, wonGift, WIN_INDEX);
  renderSlider(sliderGifts);

  const slider = document.getElementById('slide');
  await sleep(400);

  // Анимация: transition к выигрышу
  slider.style.transition = 'transform 3s cubic-bezier(0.33,1,0.68,1)';
  const targetX = -((WIN_INDEX - 1) * CARD_TOTAL); // если window слева
  // если window по центру, то targetX = -((WIN_INDEX - 1) * CARD_TOTAL)
  slider.style.transform = `translateX(${targetX}vw)`;


  await sleep(3100);
  slider.style.transition = 'none';
  renderSlider(sliderGifts, WIN_INDEX);
  slider.style.transform = `translateX(${targetX}vw)`;

  if (wonGift) {
    alert(`Поздравляем! Вы получили подарок!\n\nСсылка: ${wonGift.link}`);
  } else {
    alert('Упс, подарок не найден :(');
  }

  btn.removeAttribute('disabled');
  btn.innerText = 'Открыть';
  btn.style.backgroundColor = '#3281dc';
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

document.addEventListener('DOMContentLoaded', loadCaseData);