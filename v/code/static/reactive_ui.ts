// Wait until the entire HTML document (DOM) has fully loaded
document.addEventListener("DOMContentLoaded", (): void => {
    //
    // Get a reference to the Send button by its ID and ensure it’s an HTMLButtonElement
    const sendBtn: HTMLButtonElement | null = document.querySelector("#sendBtn");
    //
    // If the button exists in the DOM, attach an event listener to it
    if (sendBtn) {
      sendBtn.addEventListener("click", async (): Promise<void> => {
        //
        // 1️⃣ Get the user's input field and ensure it's an HTMLInputElement
        const userInput: HTMLInputElement | null = document.getElementById("userInput");
        //
        // If the input element is missing, stop execution.
        if (!userInput) return;
        //
        // Extract the value typed by the user
        const inputValue: string = userInput.value;
        //
        // 2️⃣ Send an asynchronous POST request to the backend endpoint `/process`
        // The fetch() function returns a Promise<Response>
        const response: Response = await fetch("/process", {
            //
            // Define the HTTP method.
            method: "POST",
            // 
            // Tell the backend we’re sending JSON.
            headers: { "Content-Type": "application/json" },
            // 
            // Convert the JS object to a JSON string.
            body: JSON.stringify(
                { 
                    input: inputValue 
                }
            )
        });
        //
        // 3️⃣ Await the backend’s reply as text (HTML snippet)
        const html: string = await response.text();
        //
        // 4️⃣ Find the div that will display the server response
        const responseDiv: HTMLElement | null = document.getElementById("response-div");
        //
        // If the div exists, update its content
        if (responseDiv) {
          responseDiv.innerHTML = html;
        }
        //
        // 5️⃣ We don’t reset or modify the input field
        // So the user’s typed text remains visible for context
      });
    }
  });
  