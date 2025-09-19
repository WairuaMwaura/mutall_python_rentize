"use strict";
// 
// Select all the table cells.
var my_cells = document.querySelectorAll("td");
// 
// Convert cells node list to an array.
var cells_arr = Array.from(my_cells);
// 
// Select all the table rows.
var my_rows = document.querySelectorAll("tr");
// 
// Convert cells node list to an array.
var rows_arr = Array.from(my_rows);
// 
// Select the last row of the table.
var last_row = document.querySelector('tr:last-child');
// 
// Loop through each cell and add an event listener to them.
cells_arr.forEach(function (clicked_cell) {
    clicked_cell.addEventListener("click", function () {
        // 
        // Check if the clicked cell element has a class 'selected'.
        if (clicked_cell.classList.contains('selected')) {
            // 
            // Remove the class 'selected' from clicked cell.
            clicked_cell.classList.remove("selected");
            // 
            // Remove the class 'selected_2' from the parent row.
            var parentRow = clicked_cell.closest('tr');
            if (parentRow) {
                parentRow.classList.remove('selected_2');
            }
            // 
            // Remove the 'disabled' class from the last row.
            last_row === null || last_row === void 0 ? void 0 : last_row.classList.remove('disabled');
        }
        else {
            // 
            // Check if any other cell element was selected
            cells_arr.forEach(function (cell_2) {
                // 
                // Remove the class 'selected'.
                cell_2.classList.remove('selected');
            });
            //
            // Add the class 'selected' for the clicked cell element
            clicked_cell.classList.add('selected');
            // 
            // check if any other row element was selected and remove the 'selected_2' class.
            rows_arr.forEach(function (row_2) {
                row_2.classList.remove('selected_2');
            });
            // 
            // Add the 'selected_2' class for the parent row
            var parentRow_2 = clicked_cell.closest('tr');
            if (parentRow_2) {
                parentRow_2.classList.add('selected_2');
            }
            // 
            // Add the 'disabled' class to the last row.
            last_row === null || last_row === void 0 ? void 0 : last_row.classList.add('disabled');
        }
    });
});
