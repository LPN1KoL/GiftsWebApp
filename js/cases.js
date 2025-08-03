async function loadCases() {
  try {
    const response = await fetch('/data/cases.json');
    const cases = await response.json();

    const basicContainer = document.querySelector('.basic .cases-list');
    const allinContainer = document.querySelector('.all-in .cases-list');

    // Очистим контейнеры
    basicContainer.innerHTML = '';
    allinContainer.innerHTML = '';

    cases.forEach(c => {
      // Создаем элемент кейса
      const caseDiv = document.createElement('div');
      caseDiv.className = 'case';
      caseDiv.style.cursor = 'pointer';

      caseDiv.innerHTML = `
        <div class="case-img"><img class="cimg" src="${c.logo}" alt="${c.name}"></div>
        <div class="case-name"><h3>${c.name}</h3></div>
        <div class="case-price">
          <div class="price">
            <img class="tgstar" src="data:image/svg+xml,%3csvg%20viewBox='0%200%2014%2015'%20fill='%23FFCA5A'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20fill-rule='evenodd'%20clip-rule='evenodd'%20d='M6.63869%2012.1902L3.50621%2014.1092C3.18049%2014.3087%202.75468%2014.2064%202.55515%2013.8807C2.45769%2013.7216%202.42864%2013.5299%202.47457%2013.3491L2.95948%2011.4405C3.13452%2010.7515%203.60599%2010.1756%204.24682%209.86791L7.6642%208.22716C7.82352%208.15067%207.89067%207.95951%207.81418%207.80019C7.75223%207.67116%207.61214%207.59896%207.47111%207.62338L3.66713%208.28194C2.89387%208.41581%202.1009%208.20228%201.49941%207.69823L0.297703%206.69116C0.00493565%206.44581%20-0.0335059%206.00958%200.211842%205.71682C0.33117%205.57442%200.502766%205.48602%200.687982%205.47153L4.35956%205.18419C4.61895%205.16389%204.845%204.99974%204.94458%204.75937L6.36101%201.3402C6.5072%200.987302%206.91179%200.819734%207.26469%200.965925C7.43413%201.03612%207.56876%201.17075%207.63896%201.3402L9.05539%204.75937C9.15496%204.99974%209.38101%205.16389%209.6404%205.18419L13.3322%205.47311C13.713%205.50291%2013.9975%205.83578%2013.9677%206.2166C13.9534%206.39979%2013.8667%206.56975%2013.7269%206.68896L10.9114%209.08928C10.7131%209.25826%2010.6267%209.52425%2010.6876%209.77748L11.5532%2013.3733C11.6426%2013.7447%2011.414%2014.1182%2011.0427%2014.2076C10.8642%2014.2506%2010.676%2014.2208%2010.5195%2014.1249L7.36128%2012.1902C7.13956%2012.0544%206.8604%2012.0544%206.63869%2012.1902Z'%20fill='%23FFCA5A'%3e%3c/path%3e%3c/svg%3e" alt=""> 
            <span class="cprise">${c.price}</span>
          </div>
        </div>
      `;

      // При клике — переход на страницу кейса, передаем id в параметре
      caseDiv.addEventListener('click', () => {
        window.location.href = `/templates/main.html?id=${encodeURIComponent(c.id)}`;
      });

      if (c.category === 'basic') {
        basicContainer.appendChild(caseDiv);
      } else if (c.category === 'allin') {
        allinContainer.appendChild(caseDiv);
      }
    });

  } catch (e) {
    console.error('Ошибка загрузки кейсов:', e);
  }
}

document.addEventListener('DOMContentLoaded', loadCases);
