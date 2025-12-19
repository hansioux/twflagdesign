/**
 * Hashtag Autocomplete Module
 * Handles fetching tags and showing suggestions for input fields.
 */

const Autocomplete = {
    tags: [],
    selectedIndex: -1,
    matches: [],

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
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            color: var(--color-text-main);
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
        let val = input.value;
        let cursor = input.selectionStart;

        // Find current word being typed
        // Look backwards from cursor until space or start
        let textBefore = val.slice(0, cursor);
        const lastSpace = textBefore.lastIndexOf(' ');
        let currentWord = textBefore.slice(lastSpace + 1);

        if (currentWord.length > 0 && !currentWord.startsWith('#')) {
            // Auto-prepend #
            const beforeWord = textBefore.slice(0, lastSpace + 1);
            const newTextBefore = beforeWord + '#' + currentWord;
            const textAfter = val.slice(cursor);

            input.value = newTextBefore + textAfter;

            // Adjust cursor
            cursor += 1;
            input.setSelectionRange(cursor, cursor);

            // Update local vars for filtering
            val = input.value;
            textBefore = newTextBefore;
            currentWord = '#' + currentWord;
        }

        if (currentWord.length < 1) {
            box.style.display = 'none';
            return;
        }

        // Filter tags
        this.matches = this.tags.filter(t =>
            t.toLowerCase().startsWith(currentWord.toLowerCase()) &&
            t.toLowerCase() !== currentWord.toLowerCase() // Don't suggest exact match if completed?
        );

        if (this.matches.length > 0) {
            this.showSuggestions(this.matches, input, box, currentWord);
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
        this.selectedIndex = 0;
        matches.forEach((tag, index) => {
            const div = document.createElement('div');
            div.textContent = tag;
            div.style.padding = '8px 12px';
            div.style.cursor = 'pointer';
            div.className = 'suggestion-item';

            // Hover effect
            div.onmouseover = () => { div.style.background = 'var(--color-border)'; };
            div.onmouseout = () => { div.style.background = 'var(--color-surface)'; };

            if (index === 0) div.style.background = 'var(--color-border)'; // Highlight first

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
        if (box.style.display === 'none') {
            // If Enter is pressed while box is hidden, do nothing special (allow form submit)
            return;
        }

        const items = box.querySelectorAll('.suggestion-item');
        if (items.length === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.selectedIndex++;
            if (this.selectedIndex >= items.length) this.selectedIndex = 0;
            this.updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.selectedIndex--;
            if (this.selectedIndex < 0) this.selectedIndex = items.length - 1;
            this.updateSelection(items);
        } else if (e.key === 'Enter' || e.key === 'Tab') {
            if (this.selectedIndex > -1) {
                e.preventDefault();
                this.applyTag(this.matches[this.selectedIndex], input, box);
            }
            // If nothing selected, let default behavior happen (e.g. submit form or next field)
            // But if box is open, usually Enter selects first? 
            // Current User request: "map the up and down arrow keys".
            // Let's stick to explicit selection.
        } else if (e.key === 'Escape') {
            box.style.display = 'none';
        }
    },

    updateSelection: function (items) {
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.style.background = 'var(--color-border)';
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.style.background = 'var(--color-surface)';
            }
        });
    },
};
