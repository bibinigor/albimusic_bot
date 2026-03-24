// Конфигурация: список тем, соответствующий вашим 9 файлам
const themes = [
    { id: 1, title: "💪 Энергия для спорта", img: "/img/1.jpeg", audio: "/audio/1.mp3" },
    { id: 2, title: "🧘‍♂️ Фон для релакса", img: "/img/2.jpeg", audio: "/audio/2.mp3" },
    { id: 3, title: "🕺 Зажигательный бит", img: "/img/3.jpeg", audio: "/audio/3.mp3" },
    { id: 4, title: "⚡ Саундтрек для эпичных моментов", img: "/img/4.jpeg", audio: "/audio/4.mp3" },
    { id: 5, title: "🌍 Уникальные этнические мотивы", img: "/img/5.jpeg", audio: "/audio/5.mp3" },
    { id: 6, title: "🚗 Музыка для дороги", img: "/img/6.jpeg", audio: "/audio/6.mp3" },
    { id: 7, title: "🎻 Современная классика", img: "/img/7.jpeg", audio: "/audio/7.mp3" },
    { id: 8, title: "☕ Расслабляющий лоу-фай", img: "/img/8.jpeg", audio: "/audio/8.mp3" },
    { id: 9, title: "🤖 Песня с голосом нейросети", img: "/img/9.jpeg", audio: "/audio/9.mp3" }
];

// Глобальные переменные
let currentPlayingCard = null;
const globalAudio = document.getElementById('globalAudioPlayer');

// Функция для создания HTML-карточки темы
function createThemeCard(theme) {
    const card = document.createElement('div');
    card.className = 'theme-card';
    card.dataset.id = theme.id;

    card.innerHTML = `
        <img src="${theme.img}" alt="${theme.title}" class="theme-img" loading="lazy">
        <h3 class="theme-title">${theme.title}</h3>
        <button class="play-button" data-audio="${theme.audio}" aria-label="Воспроизвести ${theme.title}">
            <i class="fas fa-play"></i>
        </button>
    `;
    return card;
}

// Функция для отрисовки всех карточек
function renderThemes() {
    const container = document.getElementById('themesContainer');
    if (!container) return;

    themes.forEach(theme => {
        const card = createThemeCard(theme);
        container.appendChild(card);
    });

    // Назначаем обработчики кнопкам воспроизведения
    document.querySelectorAll('.play-button').forEach(button => {
        button.addEventListener('click', function() {
            const audioSrc = this.getAttribute('data-audio');
            const card = this.closest('.theme-card');
            toggleAudio(audioSrc, card, this);
        });
    });
}

// Функция управления воспроизведением аудио
function toggleAudio(audioSrc, card, button) {
    const icon = button.querySelector('i');

    // Если уже играет этот трек — ставим на паузу
    if (currentPlayingCard === card && !globalAudio.paused) {
        globalAudio.pause();
        button.classList.remove('playing');
        icon.className = 'fas fa-play';
        return;
    }

    // Если играет другой трек — останавливаем его
    if (currentPlayingCard && currentPlayingCard !== card) {
        const prevButton = currentPlayingCard.querySelector('.play-button');
        const prevIcon = prevButton.querySelector('i');
        prevButton.classList.remove('playing');
        prevIcon.className = 'fas fa-play';
    }

    // Загружаем и воспроизводим новый трек
    globalAudio.src = audioSrc;
    globalAudio.play()
        .then(() => {
            currentPlayingCard = card;
            button.classList.add('playing');
            icon.className = 'fas fa-pause';

            // Когда трек закончится сам
            globalAudio.onended = function() {
                button.classList.remove('playing');
                icon.className = 'fas fa-play';
                currentPlayingCard = null;
            };
        })
        .catch(error => {
            console.error("Ошибка воспроизведения:", error);
            alert("Не удалось воспроизвести аудио. Проверьте консоль для деталей.");
        });
}

// Инициализация после загрузки страницы
document.addEventListener('DOMContentLoaded', function() {
    renderThemes();
    console.log("Лендинг ALBI Music загружен. Темы:", themes.length);
});
