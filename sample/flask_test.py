from flask import Flask, render_template
from flask import request
from procrustes.forms import forms

app = Flask(__name__)


class Pet(forms.Declarative):
    name = forms.String(name='Name')
    species = forms.String(name='Species')

class Form(forms.Declarative):
    name = forms.String(name='Your name')
    age = forms.Integer(name='Age')
    pets = forms.List(Pet)


@app.route('/', methods=['POST', 'GET'])
def hello():
    if request.form:
        form = Form(request.form, False)
        if form.is_valid():
            print 'Cool!'
            # Use form.data as validated structure
    else:
        form = Form(validate=False)
    return render_template('form.html', form=form)

if __name__ == "__main__":
    app.run()
