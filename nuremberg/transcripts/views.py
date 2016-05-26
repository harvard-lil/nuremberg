from django.shortcuts import render
from django.views.generic import View

class Search(View):
    template_name = 'transcripts/search.html'
    def get(self, request, transcript_id, *args, **kwargs):
        query = request.GET.get('query', None)
        document = {
            'id': 350,
            'title': """
Medical Case
(USA v. Karl Brandt et al. 1946-47)""",
            'literal_title': """
            The Medical Case, U.S.A. vs. Karl Brandt, et al.
(also known as the Doctors’ Trial), was prosecuted in 1946-47 against twenty-three doctors and administrators accused of organizing and participating in war crimes and crimes against humanity in the form of medical experiments and medical procedures inflicted on prisoners and civilians.
            """,
            'cases': {'all':[{'short_name': 'NMT 1'}]},
        }
        results = [
            {
                'text': """Oskar Schroeder, Karl Genzken, Karl [Geb]hardt, Kurt Blome, <mark>Rudolf</mark> <mark>Brandt</mark>, Joachim Mrugowsky, Helmut Poppendick, Wolfram Sievers, Gerhard Rose, Siegfried Ruff, Hans Wo[l]fgang Romberg, Vi[k]tor […]""",
                'page': 1,
                'count': 2,
            },
            {
                'text': """<mark>BRANDT</mark>—Personal physician to Rudolf [i.e., Adolf] Hitler, Gruppenfuehrer in the  […] Office for Medical Science and Research under the defendant Karl Brandt, Reich Commissioner for Health and Sanitation […]""",
                'page': 2,
                'count': 3,
            },
            {
                'text': """the matter of the United States of America, against Karl <mark>Brandt</mark>, et al, defendants, sitting at Nurnberg, Germany, on 9 December […] Secretary General: Karl <mark>Brandt</mark>, Siegfried Handloser, Paul Rostock, Oskar […]""",
                'page': 2,
                'count': 8,
            },
        ]
        return render(request, self.template_name, {'query': query, 'document': document, 'results': results})


class Show(View):
    template_name = 'transcripts/show.html'
    def get(self, request, transcript_id, *args, **kwargs):
        # document = Document.objects.get(id=document_id)
        document = {
            'title': """
Medical Case
(USA v. Karl Brandt et al. 1946-47)""",
            'literal_title': """
            The Medical Case, U.S.A. vs. Karl Brandt, et al.
(also known as the Doctors’ Trial), was prosecuted in 1946-47 against twenty-three doctors and administrators accused of organizing and participating in war crimes and crimes against humanity in the form of medical experiments and medical procedures inflicted on prisoners and civilians.
            """,
            'cases': {'all':[{'short_name': 'NMT 1'}]},
            'image_urls': range(1,100),
            'activities': {'count': 1, 'all':[{'short_name': 'Epidemic jaundice experiments'}]},
            'text': """
            <p>
            <em>Official Transcript of the American Military Tribunal in the matter of the United States of America, against Karl Brandt, et al, defendants, sitting at Nurnberg, Germany, on 9 December 1946, 1000-1700, Justice Beals, presiding.</em>
<p>
<strong>THE MARSHAL:</strong> Military Tribunal No. 1 is now in session. God save the United States of America and this honorable Tribunal. There will be order in the Court.
<p>
<strong>THE PRESIDENT [Beals]:</strong> The Secretary General will ascertain that all the defendants are present.
<p>
<strong>THE MARSHAL:</strong> The Secretary General will call the roll of the defendants.
<p>
(The Secretary General: Karl Brandt, Siegfried Handloser, Paul Rostock, Oskar Schroeder, Karl Genzken, Karl [Geb]hardt, Kurt Blome, Rudolf Brandt, Joachim Mrugowsky, Helmut Poppendick, Wolfram Sievers, Gerhard Rose, Siegfried Ruff, Hans Wo[l]fgang Romberg, Vi[k]tor Brack, Hermann Becker-Freyseng, Georg August Weltz, Konrad Schaefer, Waldemar Hoven, Wilhelm Beiglb[oe]ck, Adolf Pokorny, Herta Oberhauser, Fritz Fischer.)
<p>
<strong>THE SECRETARY GENERAL:</strong> All of the defendants are present and accounted for.
<p>
<strong>THE PRESIDENT:</strong> The Secretary General will note for the record the presence of the defendants.
<p>
I have two questions now to propound to the defendants. As the name of each defendant is called he will rise in his place and proceed to the center in front of the microphone and answer the questions which I shall propound to him. Karl Brandt. Your name is Karl Brandt?
<p>
<strong>KARL BRANDT:</strong> Yes.
<p>
<strong>THE PRESIDENT:</strong> Have you received and had an opportunity to read the indictment <a>[HLSL item 564]</a> filed against you?
<p>
<strong>KARL BRANDT:</strong> I have read the indictment, yes.
<p>
<strong>THE PRESIDENT:</strong> Have you entered your plea of Not Guilty to this indictment and do you now plea Not Guilty?
<p>
<strong>KARL BRANDT:</strong> Yes, I am not guilty.
<p>
<strong>THE PRESIDENT:</strong> You may be seated. Paul Rostock.
<p>
<strong>PAUL ROSTOCK:</strong> Yes.
<p>
<strong>THE PRESIDENT:</strong> Have you received and have you had an opportunity to read the indictment filed against you?

<div class="page-handle"><span class="page-number">Page 1</span></div>
<p><strong>KARL BRANDT:</strong> I have read the indictment, yes.
<p>
<strong>THE PRESIDENT:</strong> Have you entered your plea of Not Guilty to this indictment and do you now plea Not Guilty?
<p>
<strong>KARL BRANDT:</strong> Yes, I am not guilty.
<p>
<strong>THE PRESIDENT:</strong> You may be seated. Paul Rostock.
<p>
<strong>PAUL ROSTOCK:</strong> Yes.
<p>
<strong>THE PRESIDENT:</strong> Have you received and have you had an opportunity to read the indictment filed against you?

            """,
        }
        return render(request, self.template_name, {'document': document})
