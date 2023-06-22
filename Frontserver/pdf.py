def pdf_to_text_spans(src):

    import fitz
    import re
    import unicodedata

    def extract_useful_text_from_pdf(src):

        def is_useful(text):
            return not re.match(r"^(Figure|Table)\s+(\d+):", text)
        
        abstract = None # abstract span의 텍스트 정보
        def is_section(span): # span이 section title인지 검사
						# 여러 논문을 둘러본 결과 모든 section title의 텍스트 정보가 첫 페이지 abstract title의 텍스트 정보와 일치함을 확인함
						# 이를 이용해 맨 처음에 abstract의 텍스트 정보를 저장해놓고 이후 텍스트들은 이와 일치하는지 검사함으로써 section title인지 확인할 수 있음
						# 다만 이것만으로는 subsection(3이 아니라 3.1, 3.2 등)을 못 잡아냄
            return (span["size"], span["flags"]) == abstract

        useful_text = []
        doc = fitz.open(src)

        toc_span = [] # ToC를 직접 찾아야 함

        for page in doc:
            for block in page.get_text("dict")["blocks"]:

                if block['type'] == 0:
                    section = ""
                    text = ""
                    for line in block["lines"]:

                        for span in line["spans"]:
                            norm_text = unicodedata.normalize("NFKD", span["text"])

                            if not abstract and norm_text.strip() == "Abstract": # span text가 abstract인 경우
                                abstract = (span["size"], span["flags"]) # 텍스트 정보 저장
                            
                            if abstract and is_section(span): # 저장된 abstract 정보가 존재하며 현재 span의 정보가 이와 일치하면
                                section += span["text"] + " " # section title로 판단하여 더함
                            
                            text += norm_text + " "

                    if is_useful(text):
                        useful_text.append(text)
                    
                    if section: toc_span += [section.strip()] # section title을 list에 저장

        doc.close()
        return useful_text, toc_span


    extracted_text, toc = extract_useful_text_from_pdf(src)
    cnt = 0
    maxlen = len(toc)-1

    res = []
    buf = ""
    for text in extracted_text:

        if cnt < maxlen and text.strip() == toc[cnt+1]:
            if buf:
                res += [{"section": toc[cnt], "text": buf}]
                buf = ""
            cnt += 1
        
        else:
            buf += text

    res += [{"section": toc[cnt], "text": buf}]
    return res