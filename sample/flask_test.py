from flask import Flask, render_template
from flask import request
from procrustes.forms import forms

app = Flask(__name__)


class Pet(forms.Declarative):
    name = forms.String()
    species = forms.String()

class Form(forms.Declarative):
    name = forms.String()
    age = forms.Integer()
    pets = forms.List(Pet)


@app.route('/', methods=['POST', 'GET'])
def hello():
    if request.form:
        form = Form(request.form, False)
        if form.is_valid():
            print 'Cool!'
        else:
            print form.errors
    else:
        form = Form(validate=False)
    return render_template('form.html', form=form)

if __name__ == "__main__":
    app.run()
