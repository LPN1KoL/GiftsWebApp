document.addEventListener('DOMContentLoaded', () => {
    let user_id = "849307631";  // или Telegram.WebApp.initDataUnsafe.user.id

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

    if (plusButton) {
        plusButton.addEventListener('click', async () => {
            if (!user_id) {
                alert("Ошибка: Не удалось определить Telegram ID");
                return;
            }

            try {
                const result = await sendApiRequest('/api/plus', { user_id });
                alert("Запрос успешно отправлен!");
            } catch (err) {
                alert("Ошибка при отправке: " + err.message);
            }
        });
    }

    async function updateBalance() {
        try {
            const result = await sendApiRequest('/api/get_balance', { user_id });
            const balanceElement = document.getElementById('balance_display');
            if (balanceElement) {
                balanceElement.textContent = result.balance.toLocaleString();
            }
        } catch (err) {
            console.error("Ошибка при получении баланса:", err);
            const balanceElement = document.getElementById('balance_display');
            if (balanceElement) {
                balanceElement.textContent = "Ошибка";
            }
        }
    }

    updateBalance();
});
