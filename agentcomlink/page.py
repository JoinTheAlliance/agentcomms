page = """\
<!DOCTYPE html>
<html>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      background-color: #f5f5f5;
    }
    #chat-container {
      width: 400px;
      border: 1px solid #ccc;
      border-radius: 5px;
      padding: 10px;
      background-color: #fff;
      box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.05);
    }
    #messages {
      height: 500px;
      overflow-y: auto;
      margin-bottom: 10px;
      border: 1px solid #ccc;
      padding: 5px;
    }
    #chat-input {
      width: 70%;
      height: 30px;
      padding: 5px;
      border-radius: 5px;
      border: 1px solid #ccc;
    }
    #send-button {
      height: 30px;
      margin-left: 5px;
      background-color: #4caf50;
      color: white;
      border: none;
      padding: 5px 10px;
      text-align: center;
      text-decoration: none;
      display: inline-block;
      font-size: 16px;
      border-radius: 5px;
      cursor: pointer;
    }
    #upload-container {
      padding: 1em;
    }
  </style>
  <body>
    <div id="chat-container">
      <div id="messages"></div>
      <input type="text" id="chat-input" />
      <button id="send-button">Send</button>
      <div id="upload-container">
        <form id="upload-form">
          <input type="file" id="file" name="file" />
          <input type="button" value="Upload" onclick="uploadFile()" />
        </form>

        <ul id="file-list"></ul>
      </div>
    </div>
    <script type="module">
      let socket = new WebSocket("ws://0.0.0.0:8000/ws");
      socket.onmessage = function (event) {
        let message = event.data;
        let messageContainer = document.getElementById("messages");
        let newMessage = document.createElement("div");
        newMessage.textContent = message;
        messageContainer.appendChild(newMessage);
      };

      socket.onerror = function (error) {
        console.log(`[error] ${error.message}`);
      };

      let chatInput = document.getElementById("chat-input");
      let sendButton = document.getElementById("send-button");

      sendButton.onclick = function () {
        let message = chatInput.value;
        let newMessage = document.createElement("div");
        let messageContainer = document.getElementById("messages");
        newMessage.textContent = message;
        messageContainer.appendChild(newMessage);
        socket.send(message);
        chatInput.value = "";
      };

      chatInput.addEventListener("keypress", function(event) {
        if (event.keyCode === 13) {
          event.preventDefault();
          sendButton.click();
        }
      });
    </script>
    <script>
      // Rest of your script
    </script>
  </body>
</html>
"""
