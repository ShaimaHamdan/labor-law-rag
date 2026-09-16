async function askQuestion() {
    if (askQuestion.inFlight) {
        return;
    }

    const questionInput = document.getElementById("question");
    const button = document.getElementById("askButton");
    const loading = document.getElementById("loading");
    const answer = document.getElementById("answer");
    let answerText = document.querySelector("#answer .answer-text");
    const sources = document.getElementById("sources");
    const sourceList = document.getElementById("sourceList");
    const error = document.getElementById("error");
    const question = questionInput.value.trim();

    if (!question) {
        error.textContent = "الرجاء كتابة السؤال أولاً.";
        error.style.display = "block";
        return;
    }

    askQuestion.inFlight = true;

    if (!answerText) {
        answerText = document.createElement("div");
        answerText.className = "answer-text";
        answer.appendChild(answerText);
    }

    error.style.display = "none";
    answer.style.display = "none";
    sources.style.display = "none";
    button.disabled = true;
    loading.style.setProperty("--progress", "0%");
    loading.classList.add("is-loading");

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question })
        });
        if (!response.ok || !response.body) {
            throw new Error("حدث خطأ أثناء معالجة السؤال.");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let result;

        while (true) {
            const { value, done } = await reader.read();
            buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) {
                    continue;
                }
                const event = JSON.parse(line);
                if (event.type === "progress") {
                    loading.style.setProperty("--progress", `${event.value}%`);
                } else if (event.type === "error") {
                    throw new Error(event.error);
                } else if (event.type === "result") {
                    result = event;
                }
            }

            if (done) {
                break;
            }
        }

        if (!result) {
            throw new Error("حدث خطأ أثناء معالجة السؤال.");
        }

        answerText.textContent = result.answer;
        answer.style.display = "block";
        sourceList.innerHTML = "";

        if (result.sources && result.sources.length > 0) {
            result.sources.forEach(source => {
                const div = document.createElement("div");
                div.className = "source";
                const article = document.createElement("strong");
                article.textContent = source.article;

                const link = document.createElement("a");
                link.href = source.source_url || "#";
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                link.textContent = source.source || "المصدر";

                const provisionLabel = document.createElement("span");
                provisionLabel.className = "provision-label";
                provisionLabel.textContent = "النص النظامي ذي الصلة";

                const provision = document.createElement("blockquote");
                provision.className = "provision";
                provision.textContent = `“${source.text || "لا يتوفر نص المادة."}”`;

                div.append(article, link, provisionLabel, provision);
                sourceList.appendChild(div);
            });
            sources.style.display = "block";
        }
    } catch (err) {
        error.textContent = err.message;
        error.style.display = "block";
    } finally {
        button.disabled = false;
        loading.classList.remove("is-loading");
        askQuestion.inFlight = false;
    }
}
