document.addEventListener('DOMContentLoaded', () => {
    let user_id = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || "849307631";

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
                await sendApiRequest('/api/plus', { user_id });
                alert("Запрос успешно отправлен!");
            } catch (err) {
                alert("Ошибка при отправке: " + err.message);
            }
        });
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
                usernameElement.textContent = '@' + result.username;
            }

            // Обновляем аватар
            const avatarElement = document.querySelector('.user-pic img');
            if (avatarElement) {
                avatarElement.src = `/profile_picture/${user_id}.png`;
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
