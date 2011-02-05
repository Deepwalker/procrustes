from flask import Flask, render_template
from flask import request
from procrustes import forms

app = Flask(__name__)


Form = forms.Tuple(forms.String(name='Your name'), forms.Integer(name='Age'))


@app.route('/', methods=['POST', 'GET'])
def hello():
    if request.form:
        form = Form(request.form, False)
        print 'Validate'
        if form.is_valid():
            print 'Cool!'
            # Use form.data as validated structure
    else:
        form = Form(validate=False)
    return render_template('form2.html', form=form)

if __name__ == "__main__":
    app.run()

