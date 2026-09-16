from ollama import Client


INSUFFICIENT_ANSWER = "لا توجد معلومات كافية في المواد المسترجعة للإجابة عن هذا السؤال."


class OllamaLLM:
    def __init__(self, model: str, host: str, max_output_tokens: int = 384):
        self.model = model
        self.client = Client(host=host)
        self.max_output_tokens = max_output_tokens

    def _chat(self, prompt, max_output_tokens=None):
        response = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0,
                "num_predict": max_output_tokens or self.max_output_tokens,
            },
            think=False,
            keep_alive="24h",
        )
        message = response.get("message", {})
        content = message.get("content", "").strip()
        if not content:
            raise RuntimeError("Ollama returned an empty response. Check that the language model is available.")
        return content

    def normalize(self, query):
        prompt = f"""
أنت متخصص في تحويل أسئلة المستخدم إلى استعلامات مناسبة للبحث
في نظام العمل السعودي.

حوّل السؤال إلى صياغة عربية فصحى قانونية تساعد محرك البحث
على العثور على النصوص القانونية ذات الصلة.

القواعد:
1. حافظ على المعنى المقصود من السؤال.
2. استخدم المصطلحات القانونية الموجودة عادةً في نظام العمل السعودي.
3. إذا استخدم المستخدم كلمة "فصل" أو "فصلوني"، فاستخدم عند الحاجة مصطلحات مثل "إنهاء عقد العمل" أو "فصل العامل" بحسب المعنى.
4. إذا كان السؤال عن حقوق العامل، حافظ على كلمة "حقوق العامل".
5. لا تجب عن السؤال.
6. لا تضف حكمًا قانونيًا أو مادة أو مدة أو شرطًا غير موجود في السؤال.
7. لا تفترض سببًا لإنهاء العقد إذا لم يذكره المستخدم.
8. لا تغيّر الطرف المعني بالسؤال.
9. اجعل الناتج سؤالًا واحدًا مختصرًا.
10. أخرج الصياغة فقط دون شرح أو علامات اقتباس.

السؤال:
{query}
"""
        normalized = self._chat(prompt, max_output_tokens=96)
        return normalized or query.strip()

    def select(self, query, chunks):
        sources_text = "".join(
            f"\n[المصدر {i}]\nالمادة: {chunk['sequence']}\nالنص:\n{chunk['text']}\n"
            for i, chunk in enumerate(chunks, start=1)
        )
        prompt = f"""
أنت متخصص في استرجاع النصوص القانونية من نظام العمل السعودي.

مهمتك هي اختيار المواد التي ترتبط مباشرة بالسؤال.
السؤال:
{query}

المواد المسترجعة:
{sources_text}

القواعد:
1. اختر فقط المواد التي تحتوي على نص يرتبط مباشرة بالسؤال.
2. لا تختَر مادة لمجرد وجود كلمات متشابهة مع السؤال.
3. إذا كان السؤال يتضمن عدة جوانب، اختر المواد التي تغطي الجوانب التي يتناولها نظام العمل السعودي فقط.
4. لا تحاول الإجابة عن السؤال ولا تفسر المواد.
5. لا تضف أي مادة غير موجودة في القائمة.
6. إذا كانت مادة تتعلق بموضوع مختلف، فلا تختَرها.
7. لا تختَر مادة لمجرد أنها تذكر كلمات مثل العامل أو الورثة أو الوفاة؛ يجب أن يثبت نصها الحكم المطلوب في السؤال.
8. أعد أرقام المصادر المختارة فقط بهذا الشكل: 1,4,7
9. إذا لم توجد مادة تثبت الإجابة مباشرة، أعد: NONE
"""
        result = self._chat(prompt, max_output_tokens=32)
        if result.upper() == "NONE":
            return []

        selected_numbers = []
        for part in result.split(","):
            if part.strip().isdigit():
                number = int(part.strip())
                if 1 <= number <= len(chunks):
                    selected_numbers.append(number)
        return [chunks[number - 1] for number in selected_numbers]

    def generate_answer(self, query, chunks):
        if not chunks:
            return INSUFFICIENT_ANSWER

        sources_text = "".join(
            f"\n[المصدر {i}]\nالمادة: {chunk['sequence']}\nالنص:\n{chunk['text']}\n"
            for i, chunk in enumerate(chunks, start=1)
        )
        prompt = f"""
أنت مساعد قانوني متخصص في نظام العمل السعودي.

مهمتك هي الإجابة عن سؤال المستخدم اعتمادًا فقط على النصوص القانونية الموجودة في قسم SOURCES.

السؤال:
{query}

SOURCES:
{sources_text}

قواعد الإجابة الإلزامية:
1. استخدم المعلومات الموجودة في SOURCES فقط.
2. لا تستخدم أي معلومات من معرفتك العامة بالقانون أو من خارج SOURCES.
3. لا تضف أي معلومة قانونية غير مذكورة صراحةً أو بوضوح في SOURCES.
4. لا تفترض وجود مادة أو عقوبة أو غرامة أو إجراء أو حق إذا لم يذكره النص المسترجع.
5. إذا كانت المعلومات الموجودة في SOURCES غير كافية للإجابة عن السؤال، أجب حرفيًا بهذه الجملة وحدها: {INSUFFICIENT_ANSWER}
6. عند استخدام هذه الجملة، لا تضف أي مرجع أو اقتباس أو مصدر.
7. اكتب فقط المعلومات التي يثبتها نص مصدر واحد أو أكثر بشكل صريح.
8. ضع مرجعًا بعد كل جملة تتضمن معلومة قانونية بهذا الشكل: [المصدر 1]. لا تضع مرجعًا لمصدر لا يثبت الجملة مباشرة.
9. لا تستخدم عبارات مثل "عادةً" أو "غالبًا" أو "قد يكون" لاستنتاج حكم غير مذكور.
10. لا تكتب قسمًا بعنوان "المصادر" ولا تكتب روابط.
11. أجب باللغة العربية الفصحى وبأسلوب قانوني واضح ومختصر.
12. لا تكرر السؤال ولا تضف مقدمة عامة أو خاتمة أو نصائح.
13. إذا لم تستطع دعم كل جزء من السؤال بنص صريح، استخدم جملة عدم كفاية المعلومات وحدها.

أجب الآن:
"""
        answer = self._chat(prompt)
        if INSUFFICIENT_ANSWER in answer:
            return INSUFFICIENT_ANSWER
        return answer
