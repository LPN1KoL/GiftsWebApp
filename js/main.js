async function open_case(){
    btn = document.getElementById('open_case')
    btn.setAttribute('disabled', '')
    btn.innerText = 'Открываем...'
    btn.style.backgroundColor = '#255ea0'
    slider = document.getElementById('slide')
    s = ''
    for (let i = 0; i < 32; i++){
        if (i == 29){
            s += '<div class="card">asrgfxd</div>'
        }
        else{
            s+= '<div class="card"></div>'
        }
    }
    slider.innerHTML += s
    slider.classList.add('slow-move')
    slider.style.left = '-1221vw'
    await sleep(10000)
    slider.classList.remove('slow-move')
    slider.classList.add('fast-move')
    slider.style.left = '-12vw'
    slider.innerHTML = '<div class="card"></div><div class="card"></div><div class="card"></div>'
    slider.classList.remove('fast-move')
    btn.removeAttribute('disabled')
    btn.innerText = 'Открыть'
    btn.style.backgroundColor = '#3281dc'
}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
