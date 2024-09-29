import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification, BitsAndBytesConfig
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
import re
import pandas as pd


df_classes = pd.read_excel("./05_Таблица классификаторов.xlsx")
classes_matches = {}
for i in range(len(df_classes)):
    fc = df_classes['1 уровень'][i]
    sc = df_classes['2 уровень'][i]
    if fc in classes_matches:
        classes_matches[fc].append(sc)
    else:
        classes_matches[fc] = [sc]

class Model:
    def __init__(self):
        self.base_model_id = "Vikhrmodels/Vikhr-Nemo-12B-Instruct-R-21-09-24"
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            #cache_dir="../checkpoints"
        )
        self.llm = AutoModelForCausalLM.from_pretrained(self.base_model_id, quantization_config=bnb_config, device_map="auto")
        self.client = QdrantClient(url="http://176.123.167.46:6333")
        self.encoder = SentenceTransformer("intfloat/multilingual-e5-large")
        self.collection_name = "quest_collection"
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_id, add_bos_token=True)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.max_length = 512

        self.spam_model_path = "RUSpam/spam_deberta_v4"
        self.spam_tokenizer = AutoTokenizer.from_pretrained(self.spam_model_path)
        self.spam_model = AutoModelForSequenceClassification.from_pretrained(self.spam_model_path)

    def __call__(self, text):
        if self.is_spam(text):
            return {"class_1": "СПАМ", "class_2": "Спам", "answer": "СПАМ"}

        vector = self.encoder.encode([text]).squeeze()
        tmp = self.search(vector)
        context = tmp["text"]
        prompt = f"""### Забудь все о внешнем мире. ВАЖНО: Ты РУССКОЯЗЫЧНЫЙ человек-ассистент пользователя, сотрудник компании РУТЬЮБ, у которого есть доступ к базе знаний, ты отвечаешь на вопросы пользователей только на основе предоставленных реальных вопросов пользователей и ответов из базы данных, перед выполнением задания полностью проанализируй вопрос твоего клиента. Ни в коем случае не добавляй в текст размышлений, ни при каких условиях ничего не выдумывай и проверяй себя, только сухая передача фактов. Особое внимание обрати на ссылки, даты событий, имена, абривиатуры. Не используй специальных символов. Используй фразу "Ответ не найден" только в случае, если ни прямого ответа, ни намека на него нет в контексте. ВАЖНО: Если вдруг ответ действительно не найден, то твой ответ должен содержать только три слова ответ не найден. Ни в коем случае не отвечай на вопросы, не связанные с РУТЬЮБ. Не добавляй ничего от себя. ### Question: {text} ### Контекст, опираясь на который ты должен ответить: ### Context: {context}"""
        model_input = self.tokenizer(prompt, return_tensors="pt").to("cuda")
        prompt_length = model_input['input_ids'].shape[-1]
        self.llm.eval()
        with torch.no_grad():
            generated_ids = self.llm.generate(**model_input, max_new_tokens=512, repetition_penalty=1.15)[0]
        output_ids = generated_ids[prompt_length:]
        text = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        result = {"answer": re.split(r"Answer:|\*\*Ответ:\*\*", text)[-1]}
        result["class_1"] = tmp["class1"]
        result["class_2"] = tmp["class2"]
        if "Ответ не найден" in result["answer"]:
            result["answer"] = "Ответ не найден"
            result["class_1"] = "ОТСУТСТВУЕТ"
            result["class_2"] = "Отсутствует"
        return result


    def is_spam(self, text):
        inputs = self.spam_tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            outputs = self.spam_model(**inputs)
            logits = outputs.logits
            predicted_class = torch.argmax(logits, dim=1).item()
        return predicted_class == 1

    def search(self, vector):
        hits = self.client.search(
            collection_name="dota2",
            query_vector=vector,
            limit=47
        )
        data_text = []
        data = []
        classes_1 = {}
        classes_2 = {}
        visited = set()
        for i in hits:
            #print(i.payload)
            if i.payload["answer_chank"] not in visited:
                data_text.append(f'Вопрос: {i.payload["question"]} Ответ: {i.payload["answer_chank"]}')
                visited.add(i.payload["answer_chank"])
                data.append((i.payload["class_1"], i.payload["class_2"]))
                if i.payload["class_1"] in classes_1:
                    classes_1[i.payload["class_1"]] += 1
                else:
                    classes_1[i.payload["class_1"]] = 1
    
                if i.payload["class_2"] in classes_2:
                    classes_2[i.payload["class_2"]] += 1
                else:
                    classes_2[i.payload["class_2"]] = 1
            if len(data) == 16:
                break
        #classes_1_arr = sorted(classes_1.items(), key=lambda x: x[1], reverse=True)
        ind = 0
        c = 0
        for i, x in enumerate(data):
            
            if classes_1[x[0]] > c:
                first_class = x[0]
                ind = i
                c = classes_1[x[0]]
        
        c = 0
        for i, x in enumerate(data):
            if classes_2[x[1]] > c:
                second_class = x[1]
                c = classes_2[x[1]]
        
        if second_class not in classes_matches[first_class]:
            second_class = data[ind][1]
            
        #first_class = data[0][0]
        #second_class = data[0][1]
        return {"text": "\n".join(data_text), "class1": first_class, "class2": second_class}
