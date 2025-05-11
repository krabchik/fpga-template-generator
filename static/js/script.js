// Функция преобразования списка полей формы в словарь (объект)
function getFormData($form) {
    var unindexed_array = $form.serializeArray();
    var indexed_array = {};

    $.map(unindexed_array, function(n, i){
        if (n['value'] == 'on') {
            indexed_array[n['name']] = true;
        } else if (n['value'] == 'off') {
            indexed_array[n['name']] = false;
        } else {
            indexed_array[n['name']] = n['value'];
        }
    });

    return indexed_array;
}


document.addEventListener('DOMContentLoaded', async () => {
    const boardSelect = document.getElementById('board-select');
    const boardNameDisplay = document.getElementById('board-name-display');

    const form = document.getElementById('board-form');
    const boardNameInput = document.getElementById('form-board');

    const submitButton = document.getElementById('submit-button');
    const downloadButton = document.getElementById('download-button');

    const imageContainer = document.querySelector('.image-container');
    const mainImage = document.getElementById('main-image');

    const boardExtras = document.getElementById('board-extras');
    const boardComponents = document.getElementById('board-components');
    const changeEvent = new Event('change');
    const selectedRegions = new Set();
    let lastSubmittedRegions = new Set();
    let fileIsOutdated = true;
    let filePath = null;

    const boardNamesResponse = await fetch(`/get-boards-names`);
    console.log(boardNamesResponse);
    const boardNames = await boardNamesResponse.json();
    console.log(boardNames);

    boardNames.forEach(board => {
        const option = document.createElement('option');
        option.value = board;
        option.textContent = board;
        boardSelect.appendChild(option);
    });

    // Функция отображения дополнительных параметров
    function renderExtras(extras) {
        $('#board-extras').empty();

        for (let extra_name in extras) {
            extra = extras[extra_name];
            console.log(extra);
            const input_el = document.createElement('input');
            boardExtras.appendChild(input_el);
            input_el.setAttribute('name', 'extra-' + extra_name);
            input_el.setAttribute('id', 'extra-' + extra_name);

            if (extra.type == 'bool') {
                input_el.setAttribute('type', 'checkbox');
                input_el.checked = extra.default;
            }

            const label_el = document.createElement('label');
            label_el.setAttribute('for','extra-' + extra_name);
            label_el.innerText = extra.label;
            boardExtras.appendChild(label_el);
        }
    }

    // Функция отображения компонентов платы
    function renderComponents(components) {
        $('#board-components').empty();

        for (let [component_name, component] of Object.entries(components)) {
            const input_el = document.createElement('input');
            boardComponents.appendChild(input_el);

            input_el.setAttribute('name', 'component-' + component_name);
            input_el.setAttribute('id', 'component-' + component_name);
            input_el.setAttribute('type', 'checkbox');
            input_el.checked = component.default;

            const label_el = document.createElement('label');
            label_el.setAttribute('for','component-' + component_name);
            label_el.innerText = component.label;
            boardComponents.appendChild(label_el);

            component.coordinates.forEach((coordinates, index) => {
                const regionElement = document.createElement('div');
                regionElement.classList.add('region');
                if (component.default) {
                    regionElement.classList.add('selected');
                }
                regionElement.style.left = `${coordinates.x}px`;
                regionElement.style.top = `${coordinates.y}px`;
                regionElement.style.width = `${coordinates.width}px`;
                regionElement.style.height = `${coordinates.height}px`;
                regionElement.setAttribute('data-name', component.label);
                regionElement.setAttribute('data-id', index);
                regionElement.addEventListener('click', () => {
                    if (input_el.checked) {
                        input_el.checked = false;
                        regionElement.classList.remove('selected');
                    } else {
                        input_el.checked = true;
                        regionElement.classList.add('selected');
                    }
                    input_el.dispatchEvent(changeEvent);
                });

                input_el.addEventListener('change', () => {
                    if (input_el.checked) {
                        regionElement.classList.add('selected');
                    } else {
                        regionElement.classList.remove('selected');
                    }
                })

                imageContainer.appendChild(regionElement);
            });
        }
    }

    // Функция загрузки данных платы по имени
    async function loadBoardData(boardName) {
        fileIsOutdated = true;
        console.log('Get board' + boardName);
        const response = await fetch(`/get-board?board=${encodeURIComponent(boardName)}`);
        const data = await response.json();
        mainImage.src = `/static/img/${data.image}`;
        boardNameDisplay.textContent = `Board: ${boardName}`;
        boardNameInput.value = boardName;

        selectedRegions.clear();
        document.querySelectorAll('.region').forEach(el => el.remove());

        console.log(data);

        renderExtras(data.extras);
        renderComponents(data.components);
    }

    // Загружаем данные платы при изменении выбора платы
    boardSelect.addEventListener('change', () => {
        loadBoardData(boardSelect.value);
        fileIsOutdated = true;
    });

    submitButton.addEventListener('click', async () => {
        form_data = getFormData($(form));
        const renderResponse = await fetch('/render-board', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(form_data)
        });

        if (renderResponse.ok) {
            const renderResponseJson = await renderResponse.json();
            filePath = renderResponseJson.file_path;
            downloadButton.style.display = 'inline-block';
            fileIsOutdated = false;
            console.log(filePath);
        } else {
            fileIsOutdated = true;
            alert('Ошибка при отправке данных');
        }
    });

    downloadButton.addEventListener('click', () => {
        if (fileIsOutdated) {
            downloadButton.style.display = 'none';
        } else {
            window.open('/download-file', '_blank').focus();
        }
    });

    // Инициализация первой платы
    if (boardNames) {
        loadBoardData(boardNames[0]);
    } else {
        console.log('No boards available!')
    }
});
