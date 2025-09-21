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
    clicked_cell.addEventListener("click", function() {
        // 
        // Set apart this logic for cells that are not in the last row
        if (clicked_cell.closest('tr') != last_row) {
            // 
            // Check if the clicked cell element has a class 'selected'.
            if (clicked_cell.classList.contains('selected')) {
                // 
                // Remove the class 'selected' from clicked cell.
                clicked_cell.classList.remove("selected");
                // 
                // Remove the class 'selected_2' from the parent row.
                const parentRow: HTMLTableRowElement | null = clicked_cell.closest('tr')
                if (parentRow) {
                    parentRow.classList.remove('selected_2')
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
                    // Remove the class 'selected'.
                    cell_2.classList.remove('selected');
                });
                //
                // Add the class 'selected' for the clicked cell element
                clicked_cell.classList.add('selected');
                // 
                // check if any other row element was selected and remove the 'selected_2' class.
                rows_arr.forEach((row_2) => {
                    row_2.classList.remove('selected_2');
                });
                // 
                // Add the 'selected_2' class for the parent row
                const parentRow_2: HTMLTableRowElement | null = clicked_cell.closest('tr')
                if (parentRow_2) {
                    parentRow_2.classList.add('selected_2')
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
            // Check if the clicked cell element has a class 'selected'.
            if (clicked_cell.classList.contains('selected')) {
                // 
                // Remove the class 'selected' from clicked cell.
                clicked_cell.classList.remove("selected");
                // 
                // Remove the class 'selected_2' from the last row.
                if (last_row) {
                    last_row.classList.remove('selected_2')
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
                    // Remove the class 'selected'.
                    cell_2.classList.remove('selected');
                });
                //
                // Add the class 'selected' for the clicked cell element
                clicked_cell.classList.add('selected');
                // 
                // check if any other row element was selected and remove the 'selected_2' class.
                rows_arr.forEach((row_2) => {
                    row_2.classList.remove('selected_2');
                });
                // 
                // Add the 'selected_2' class for the last row
                if (last_row) {
                    last_row.classList.add('selected_2')
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
    });
});