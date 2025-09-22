"use strict";
// 
// Select all the table cells.
const my_cells: NodeListOf<HTMLTableCellElement> = document.querySelectorAll("td");
// 
// Convert cells node list to an array.
const cells_arr: Array<HTMLTableCellElement> = Array.from(my_cells);
// 
// Select all the table rows.
const my_rows: NodeListOf<HTMLTableRowElement> = document.querySelectorAll("tr");
// 
// Convert cells node list to an array.
const rows_arr: Array<HTMLTableRowElement> = Array.from(my_rows);
// 
// Select the last row of the table.

const last_row: HTMLTableRowElement | null = document.querySelector('tr:last-child')
// 
// Loop through each cell and add an event listener to them.
cells_arr.forEach((clicked_cell: HTMLTableCellElement) => {
    clicked_cell.onclick = function() {
        // 
        // Set apart this logic for cells that are not in the last row
        if (clicked_cell.closest('tr') != last_row) {
            // 
            // Check if the clicked cell element has a class 'active-cell'.
            if (clicked_cell.classList.contains('active-cell')) {
                // 
                // Remove the class 'selected' from clicked cell.
                clicked_cell.classList.remove("active-cell");
                // 
                // Remove the class 'active-row' from the parent row.
                const parentRow: HTMLTableRowElement | null = clicked_cell.closest('tr')
                if (parentRow) {
                    parentRow.classList.remove('active-row')
                }
                // 
                // Remove the 'disabled' class from the last row.
                last_row?.classList.remove('disabled')
            }
            else {
                // 
                // Check if any other cell element was selected
                cells_arr.forEach((cell_2) => {
                    // 
                    // Remove the class 'active-cell'.
                    cell_2.classList.remove('active-cell');
                });
                //
                // Add the class 'active-cell' for the clicked cell element
                clicked_cell.classList.add('active-cell');
                // 
                // check if any other row element was selected and remove the 'active-row' class.
                rows_arr.forEach((row_2) => {
                    row_2.classList.remove('active-row');
                });
                // 
                // Add the 'active-row' class for the parent row
                const parentRow_2: HTMLTableRowElement | null = clicked_cell.closest('tr')
                if (parentRow_2) {
                    parentRow_2.classList.add('active-row')
                }
                // 
                // Add the 'disabled' class to the last row.
                last_row?.classList.add('disabled')
            } 
        }
        // 
        // Logic for last row
        else {
            //
            // Check if the clicked cell element has a class 'active-cell'.
            if (clicked_cell.classList.contains('active-cell')) {
                // 
                // Remove the class 'active-cell' from clicked cell.
                clicked_cell.classList.remove("active-cell");
                // 
                // Remove the class 'active-row' from the last row.
                if (last_row) {
                    last_row.classList.remove('active-row')
                }
                // 
                // Add the 'disabled' class to the other rows that are not the last row.
                rows_arr.forEach((row: HTMLTableRowElement) => {
                    if (row != last_row) {
                        row.classList.remove('disabled')
                    }
                });
            }
            else {
                // 
                // Check if any other cell element was selected
                cells_arr.forEach((cell_2) => {
                    // 
                    // Remove the class 'active-cell'.
                    cell_2.classList.remove('active-cell');
                });
                //
                // Add the class 'active-cell' for the clicked cell element
                clicked_cell.classList.add('active-cell');
                // 
                // check if any other row element was selected and remove the 'active-row' class.
                rows_arr.forEach((row_2) => {
                    row_2.classList.remove('active-row');
                });
                // 
                // Add the 'active-row' class for the last row
                if (last_row) {
                    last_row.classList.add('active-row')
                }
                // 
                // Add the 'disabled' class to the other rows that are not the last row.
                rows_arr.forEach((row: HTMLTableRowElement) => {
                    if (row != last_row) {
                        row.classList.add('disabled')
                    }
                });
            } 
        }
    };
});