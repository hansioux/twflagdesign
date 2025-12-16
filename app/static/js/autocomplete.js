/**
 * Hashtag Autocomplete Module
 * Handles fetching tags and showing suggestions for input fields.
 */

const Autocomplete = {
    tags: [],

    // Initialize for specific input ID
    init: function (inputId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        // Create suggestion box
        const suggestionBox = document.createElement('div');
        suggestionBox.id = inputId + '-suggestions';
        suggestionBox.className = 'autocomplete-suggestions';
        suggestionBox.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: none;
            z-index: 1000;
            max-height: 200px;
            overflow-y: auto;
            min-width: 150px;
        `;
        document.body.appendChild(suggestionBox);

        // Fetch tags once
        if (this.tags.length === 0) {
            fetch('/api/hashtags')
                .then(res => res.json())
                .then(data => {
                    this.tags = data;
                })
                .catch(err => console.error('Error fetching tags:', err));
        }

        input.addEventListener('input', (e) => this.handleInput(e, input, suggestionBox));
        input.addEventListener('keydown', (e) => this.handleKeydown(e, input, suggestionBox));

        // Close on click outside
        document.addEventListener('click', (e) => {
            if (e.target !== input && e.target !== suggestionBox) {
                suggestionBox.style.display = 'none';
            }
        });
    },

    handleInput: function (e, input, box) {
        const val = input.value;
        const cursor = input.selectionStart;

        // Find current word being typed
        // Look backwards from cursor until space or start
        const textBefore = val.slice(0, cursor);
        const lastSpace = textBefore.lastIndexOf(' ');
        const currentWord = textBefore.slice(lastSpace + 1);

        if (currentWord.length < 1) {
            box.style.display = 'none';
            return;
        }

        // Filter tags
        const matches = this.tags.filter(t =>
            t.toLowerCase().startsWith(currentWord.toLowerCase()) &&
            t.toLowerCase() !== currentWord.toLowerCase() // Don't suggest exact match if completed?
        );

        if (matches.length > 0) {
            this.showSuggestions(matches, input, box, currentWord);
        } else {
            box.style.display = 'none';
        }
    },

    showSuggestions: function (matches, input, box, currentWord) {
        const rect = input.getBoundingClientRect();
        // Simple positioning below input
        // A better approach would calculate position of the cursor, but fixed below input is safer for now.
        box.style.left = rect.left + window.scrollX + 'px';
        box.style.top = rect.bottom + window.scrollY + 'px';
        box.style.display = 'block';

        box.innerHTML = '';
        matches.forEach((tag, index) => {
            const div = document.createElement('div');
            div.textContent = tag;
            div.style.padding = '8px 12px';
            div.style.cursor = 'pointer';
            div.className = 'suggestion-item';

            // Hover effect
            div.onmouseover = () => { div.style.background = '#f1f5f9'; };
            div.onmouseout = () => { div.style.background = 'white'; };

            if (index === 0) div.style.background = '#e0f2fe'; // Highlight first

            div.onclick = () => this.applyTag(tag, input, box);
            box.appendChild(div);
        });
    },

    applyTag: function (tag, input, box) {
        const cursor = input.selectionStart;
        const val = input.value;
        const textBefore = val.slice(0, cursor);
        const lastSpace = textBefore.lastIndexOf(' ');

        const newTextBefore = textBefore.slice(0, lastSpace + 1) + tag + ' ';
        const textAfter = val.slice(cursor);

        input.value = newTextBefore + textAfter;
        // Move cursor to end of inserted tag
        const newCursor = newTextBefore.length;
        input.setSelectionRange(newCursor, newCursor);
        input.focus();

        box.style.display = 'none';
    },

    handleKeydown: function (e, input, box) {
        if (box.style.display === 'block') {
            if (e.key === 'Tab' || e.key === 'Enter') {
                e.preventDefault();
                // Select first suggestion
                const first = box.querySelector('.suggestion-item');
                if (first) {
                    first.click();
                }
            } else if (e.key === 'Escape') {
                box.style.display = 'none';
            }
        }
    }
};
