import subprocess
import time

# Código de JavaScript como una cadena
create_temporal_js = """const qrcode = require('qrcode-terminal');
const { Client } = require('whatsapp-web.js');
const fetch = require('node-fetch');
const fs = require('fs');

const client = new Client();
let conversationActive = false;
let conversationTimeout;
let currentNews = [];
let waitingForSelection = false;
let lastMessage;
let lastMessageTimestamp;
let handleNewsTimeout;

function closeConversationDueToInactivity() {
    if (conversationActive) {
        conversationActive = false;
        waitingForSelection = false;
        currentNews = [];
        client.sendMessage(lastMessage.from, 'Parece que te has ido, nuestra conversación ha finalizado debido a la inactividad. Si necesitas más información, no dudes en escribirme.');
    }
}

function checkConversationTimeout() {
    const inactivityTime = 50000; // 2.5 minutos de inactividad

    const elapsedTime = new Date().getTime() - lastMessageTimestamp;

    if (conversationActive && elapsedTime > inactivityTime) {
        closeConversationDueToInactivity();
    } else if (!conversationActive && !waitingForSelection && elapsedTime > inactivityTime) {
        // ...
    }
}

function restartConversation() {
    conversationActive = true;
    restartConversationTimeout();
}

function restartConversationTimeout() {
    clearInterval(conversationTimeout);
    conversationTimeout = setInterval(checkConversationTimeout, 10000); // Verificar cada 10 segundos
}

function respondToMessage(message) {
    lastMessageTimestamp = new Date().getTime();

    const greetings = ["Hola", "Buenos días", "Buenas tardes", "Buenas noches", "Buenas", "Qué tal", "Saludos", "Buenos dias", "buenos dias", "buenas tardes", "Que tal", "qué tal", , "que tal", "hola"];
    const userMessage = message.body.toLowerCase();
    const containsGreeting = greetings.some(greeting => userMessage.includes(greeting.toLowerCase()));

    if (containsGreeting || (!conversationActive && !waitingForSelection)) {
        if (!conversationActive && !containsGreeting && !waitingForSelection) {
            // Si la conversación está inactiva y no contiene saludo, realizar búsqueda directa
            handleNewsRequest(message);
            restartConversationTimeout(); // Reiniciar el temporizador cuando se recibe un mensaje
        } else {
            if (!conversationActive && !waitingForSelection) {
                client.sendMessage(message.from, "Hola, soy tu asistente vistual, que quieres saber hoy");
            }
            restartConversation(); // Reiniciar la conversación cuando se detecta un saludo o cuando la conversación está inactiva
        }
    } else {
        handleNewsRequest(message);
        restartConversationTimeout(); // Reiniciar el temporizador cuando se recibe un mensaje
    }
}

function closeConversation() {
    if (conversationActive) {
        conversationActive = false;
        waitingForSelection = false;
        currentNews = [];
        if (lastMessage && client && conversationTimeout) {
            clearTimeout(conversationTimeout);
            client.sendMessage(lastMessage.from, 'Bien, si no necesitas más nada por ahora, un placer ayduarte')
                .then(() => {
                    lastMessage = null; // Limpiar el último mensaje después de enviar el cierre
                })
                .catch(err => {
                    console.error('Error al enviar mensaje:', err);
                });
        }
    } else {
        if (lastMessage) {
            client.sendMessage(lastMessage.from, 'Parece que te has ido, nuestra conversación ha finalizado. Si necesitas más información, aqui estare para ti.');
        }
    }
}

function resetTimeout() {
    clearTimeout(conversationTimeout);
    conversationTimeout = setTimeout(() => {
        closeConversation();
        if (!conversationActive && lastMessage && lastMessageTimestamp && (new Date().getTime() - lastMessageTimestamp) < 150000) {
            respondToMessage(lastMessage);
        }
    }, 50000);
}

function handleNewsRequest(message) {
    function closeAfterInactivity() {
        if (conversationActive) {
            conversationActive = false;
            waitingForSelection = false;
            currentNews = [];
            client.sendMessage(lastMessage.from, 'Parece que te has ido, espero que te haya sido de ayuda. Te veo luego');
        }
    }

    if (!waitingForSelection) {
        clearTimeout(handleNewsTimeout);

        const tema = message.body;
        const apiKey = '595eee166d36401fad4c811c29767f8e';
        const url = `https://newsapi.org/v2/everything?q=${encodeURIComponent(tema)}&sortBy=popularity&apiKey=${apiKey}`;

        fetch(url)
            .then(response => response.json())
            .then(newsData => {
                if (newsData.articles && newsData.articles.length > 0) {
                    currentNews = newsData.articles;
                    const headlines = currentNews.slice(0, 5).map((article, index) => `${index + 1}. ${article.title}.\n\n`);
                    const responseMessage = `Aquí te traigo lo mas importante:\n\n${headlines.join('')}6. No deseo leer ninguna de estas fuentes.`;

                    client.sendMessage(message.from, responseMessage);
                    waitingForSelection = true;

                    handleNewsTimeout = setTimeout(closeAfterInactivity, 50000);
                } else {
                    client.sendMessage(message.from, `No se encontraron noticias sobre "${tema}".`);
                    handleNewsTimeout = setTimeout(closeAfterInactivity, 50000);
                }
            })
            .catch(error => {
                console.error('Error al obtener noticias:', error);
                client.sendMessage(message.from, 'Lo siento, ocurrió un error al obtener noticias.');
                handleNewsTimeout = setTimeout(closeAfterInactivity, 50000);
            });
    }
}

client.on('qr', qr => {
    qrcode.generate(qr, { small: true });
    const htmlContent = `<html>
    <head>
        <title>WhatsApp QR Code</title>
    </head>
    <body>
        <div id="qrcode"></div>
        <script src="https://cdn.rawgit.com/davidshimjs/qrcodejs/gh-pages/qrcode.min.js"></script>
        <script>
            var qrcode = new QRCode(document.getElementById("qrcode"), {
                text: "${qr}",
                width: 256,
                height: 256,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
        </script>
    </body>
    </html>`;

    fs.writeFileSync('index.html', htmlContent, (err) => {
        if (err) throw err;
        console.log('QR code generated and saved in index.html');
    });
});

client.on('ready', () => {
    console.log('Cliente logueado!!!');

    client.on('message', message => {
        clearTimeout(conversationTimeout);
        lastMessageTimestamp = new Date().getTime();
        lastMessage = message;
    
        if (!conversationActive) {
            // Si la conversación está inactiva, responder al mensaje recibido para reanudar la conversación
            respondToMessage(message);
        } else {
            // Si la conversación está activa, manejar el mensaje según la lógica actual
            handleNewsRequest(message);
        }
    });

    client.on('disconnected', (reason) => {
        console.log('Cliente desconectado. Razón:', reason);
        process.exit(0);
    });
});

client.on('message', async message => {
    const selectedOption = parseInt(message.body);

    if (waitingForSelection && !isNaN(selectedOption)) {
        if (selectedOption === 6) {
            client.sendMessage(message.from, 'No hay problema, dime qué otra información quieres.')
                .then(() => {
                    waitingForSelection = false;
                    clearTimeout(handleNewsTimeout);
                    return;
                })
                .catch(err => {
                    console.error('Error al enviar mensaje:', err);
                });
        } else {
            const selectedNewsIndex = selectedOption - 1;
            if (selectedNewsIndex >= 0 && selectedNewsIndex < currentNews.length) {
                const selectedArticle = currentNews[selectedNewsIndex];
                const articleMessage = `Seleccionaste esta noticia:\n\n${selectedArticle.title}.\n\n${selectedArticle.description}\n\nLeer más: ${selectedArticle.url}\n\nSi necesitas mas información en específico sobre algún tema no dudes en preguntar.`;

                client.sendMessage(message.from, articleMessage)
                    .then(() => {
                        waitingForSelection = false;
                    })
                    .catch(err => {
                        console.error('Error al enviar mensaje:', err);
                    });
            } else {
                client.sendMessage(message.from, 'Por favor, responda con un número válido del artículo que desea leer:');
            }
        }
    }
});

client.initialize();

"""

# Guardar el código en un archivo temporal
with open("temporal.js", "w", encoding='utf-8') as js_file:
    js_file.write(create_temporal_js)

# Añadir un pequeño retraso antes de ejecutar el script de Node.js
time.sleep(2)

# Llamada al proceso Node.js con el script temporal
subprocess.run(["node", "temporal.js"])
