    document.addEventListener('DOMContentLoaded', function() {
        const dropdownArrow = document.getElementById('dropdownArrow');
        const dropdownMenu = document.getElementById('dropdownMenu');

        if (dropdownArrow && dropdownMenu) {
            // Открытие/закрытие меню по клику на стрелочку
            dropdownArrow.addEventListener('click', function(e) {
                e.stopPropagation();
                dropdownMenu.classList.toggle('active');
                dropdownArrow.classList.toggle('active-arrow');
            });

            // Закрытие меню при клике в любую другую точку экрана
            document.addEventListener('click', function(e) {
                if (!dropdownMenu.contains(e.target) && !dropdownArrow.contains(e.target)) {
                    dropdownMenu.classList.remove('active');
                }
            });
        }
    });
