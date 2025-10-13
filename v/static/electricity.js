"use strict";
document.addEventListener("DOMContentLoaded", () => {
    //
    // Step 1: Select the "Generate" button element from the HTML document using its ID.
    // This allows you to access and interact with the button element from the JavaScript code.
    const generate_btn = document.querySelector("#generate");
    // 
    // Step 2: Attach a "click" event listener to the Generate button.
    // This ensures that when the user clicks the button, a specific function (the callback) runs to process the request.
    if (generate_btn) {
        generate_btn.onclick = async () => {
            //
            // Step 3: Select the input field elements where the user enters their data.
            const month_field = document.querySelector("#month");
            const year_field = document.querySelector("#year");
            //
            // Step 4: Retrieve the actual values typed by the user in the input fields.
            if (month_field && year_field) {
                const month_value = month_field.value;
                const year_value = year_field.value;
                //
                // Call the function to fetch and display bills
                await get_all_ebills(month_value, year_value);
            }
        };
    }
    // 
    // Step 5: Define an asynchronous callback function responsible for handling the fetch request logic.
    // The 'async' keyword allows us to use 'await' inside, making asynchronous code behave more like synchronous code.
    async function get_all_ebills(month_value, year_value) {
        // Step 6: Convert the user's input into a JSON string using JSON.stringify().
        // This serialization ensures the data is in the correct format for transmission over HTTP.
        const user_input_json = JSON.stringify({
            month: month_value,
            year: year_value
        });
        // 
        // Step 7: Use the fetch() API to send a POST request to the FastAPI backend at the '/all_ebills' endpoint.
        // The fetch() method returns a Promise, so we use 'await' to pause execution until the server responds.
        // Include the JSON-encoded input in the request body, and set the appropriate 'Content-Type' header to 'application/json'.
        const response = await fetch("/all_ebills", {
            //
            // Define the HTTP method.
            method: "POST",
            // 
            // Tell the backend we’re sending JSON.
            headers: { "Content-Type": "application/json" },
            // 
            // Convert the JS object to a JSON string.
            body: user_input_json
        });
        // 
        // Step 8: Since the FastAPI '/all_ebills' endpoint returns HTML (not JSON),
        // use response.text() instead of response.json() to get the HTML content as a string.
        // Store this HTML string in a variable for later use.
        const html_table = await response.text();
        console.log(html_table);
        // 
        // Step 9: Locate the 'all_ebills' <div> in the DOM where you want to display the server's response.
        // This div serves as the target container for dynamically inserted HTML.
        const all_ebills_div = document.querySelector("#all_ebills");
        // 
        // Step 10: Insert the returned HTML into the 'service_content' div using the innerHTML property.
        // This effectively updates only that section of the page, avoiding a full-page reload.
        if (all_ebills_div) {
            all_ebills_div.innerHTML = html_table;
        }
    }
    // 
    // Select the 'client' button.
    const client_btn = document.querySelector("#client");
    // 
    // Attach the click event to the 'client' button.
    if (client_btn) {
        client_btn.onclick = async () => {
            // 
            // Select the input fields.
            const month_field = document.querySelector("#month");
            const year_field = document.querySelector("#year");
            // 
            // Validate that the input fields have values and use them to fetch the client ebills
            if (month_field && year_field) {
                const month_value = month_field.value;
                const year_value = year_field.value;
                await get_client_ebills(month_value, year_value);
            }
        };
    }
    // 
    // Create the callback function to the 'client' button that requests for the data from the server.
    async function get_client_ebills(month_value, year_value) {
        // 
        // Convert the user input to JSON.
        const user_input_json = JSON.stringify({
            month: month_value,
            year: year_value
        });
        // 
        // Send a  fetch request to the server and save the response.
        const response = await fetch("/client_ebills", {
            //
            // Define the HTTP method.
            method: "POST",
            // 
            // Tell the backend we’re sending JSON.
            headers: { "Content-Type": "application/json" },
            // 
            // Convert the JS object to a JSON string.
            body: user_input_json
        });
        //
        // Get the HTML table sent by FastAPI
        const html_table = await response.text();
        console.log(html_table);
        // 
        // Render the returned HTML above in the 'service_content' div.
        const service_content_div = document.querySelector("#service_content");
        // 
        // Step 10: Insert the returned HTML into the 'service_content' div using the innerHTML property.
        // This effectively updates only that section of the page, avoiding a full-page reload.
        if (service_content_div) {
            service_content_div.innerHTML = html_table;
        }
    }
    // 
    // Select the 'unattended' button.
    const unattended_btn = document.querySelector("#unattended");
    // 
    // Attach the click event to the 'unattended' button.
    if (unattended_btn) {
        unattended_btn.onclick = async () => {
            // 
            // Select the input fields.
            const month_field = document.querySelector("#month");
            const year_field = document.querySelector("#year");
            // 
            // Validate that the input fields have values and use them to fetch the unattended ebills
            if (month_field && year_field) {
                const month_value = month_field.value;
                const year_value = year_field.value;
                await get_unattended_ebills(month_value, year_value);
            }
        };
    }
    // 
    // Create the callback function to the 'unattended' button that requests for the data from the server.
    async function get_unattended_ebills(month_value, year_value) {
        // 
        // Convert the user input to JSON.
        const user_input_json = JSON.stringify({
            month: month_value,
            year: year_value
        });
        // 
        // Send a  fetch request to the server and save the response.
        const response = await fetch("/unattended_ebills", {
            //
            // Define the HTTP method.
            method: "POST",
            // 
            // Tell the backend we’re sending JSON.
            headers: { "Content-Type": "application/json" },
            // 
            // Convert the JS object to a JSON string.
            body: user_input_json
        });
        //
        // Get the HTML table sent by FastAPI
        const html_table = await response.text();
        console.log(html_table);
        // 
        // Render the returned HTML above in the 'service_content' div.
        const service_content_div = document.querySelector("#service_content");
        if (service_content_div) {
            service_content_div.innerHTML = html_table;
        }
    }
    // 
    // Select the 'service' button.
    const service_btn = document.querySelector("#service");
    // 
    // Attach the click event to the 'unattended' button.
    if (service_btn) {
        service_btn.onclick = async () => {
            // 
            // Select the input fields.
            const month_field = document.querySelector("#month");
            const year_field = document.querySelector("#year");
            // 
            // Validate that the input fields have values and use them to fetch the service ebills
            if (month_field && year_field) {
                const month_value = month_field.value;
                const year_value = year_field.value;
                await get_service_ebills(month_value, year_value);
            }
        };
    }
    // 
    // Create the callback function to the 'unattended' button that requests for the data from the server.
    async function get_service_ebills(month_value, year_value) {
        // 
        // Convert the user input to JSON.
        const user_input_json = JSON.stringify({
            month: month_value,
            year: year_value
        });
        // 
        // Send a  fetch request to the server and save the response.
        const response = await fetch("/service_ebills", {
            //
            // Define the HTTP method.
            method: "POST",
            // 
            // Tell the backend we’re sending JSON.
            headers: { "Content-Type": "application/json" },
            // 
            // Convert the JS object to a JSON string.
            body: user_input_json
        });
        //
        // Get the HTML table sent by FastAPI
        const html_table = await response.text();
        console.log(html_table);
        // 
        // Render the returned HTML above in the 'service_content' div.
        const service_content_div = document.querySelector("#service_content");
        if (service_content_div) {
            service_content_div.innerHTML = html_table;
        }
    }
});
