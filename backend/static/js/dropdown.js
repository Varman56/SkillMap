    document.addEventListener('DOMContentLoaded', function() {
        const dropdownArrow = document.getElementById('dropdownArrow');
        // Раньше меню открывалось только по клику на стрелочку — теперь клик
        // на саму аватарку тоже должен его открывать (id добавлен в
        // base.html на .profile-avatar).
        const dropdownAvatar = document.getElementById('profileAvatarBtn');
        const dropdownMenu = document.getElementById('dropdownMenu');

        if (dropdownMenu && (dropdownArrow || dropdownAvatar)) {
            function toggleDropdown(e) {
                e.stopPropagation();
                dropdownMenu.classList.toggle('active');
                if (dropdownArrow) {
                    dropdownArrow.classList.toggle('active-arrow');
                }
            }

            if (dropdownArrow) {
                dropdownArrow.addEventListener('click', toggleDropdown);
            }
            if (dropdownAvatar) {
                dropdownAvatar.addEventListener('click', toggleDropdown);
            }

            // Закрытие меню при клике в любую другую точку экрана — теперь
            // проверяем клик и по стрелочке, и по аватарке, иначе клик по
            // аватарке открывал бы меню и тут же сам его закрывал этим же
            // обработчиком.
            document.addEventListener('click', function(e) {
                const clickedTrigger =
                    (dropdownArrow && dropdownArrow.contains(e.target)) ||
                    (dropdownAvatar && dropdownAvatar.contains(e.target));
                if (!dropdownMenu.contains(e.target) && !clickedTrigger) {
                    dropdownMenu.classList.remove('active');
                }
            });
        }
    });
