'use strict'

const schemaFieldsDiv = document.getElementById('schemaFields')
const fieldSelectorForm = document.getElementById('fieldSelectorForm')
const getFields = () => schemaFieldsDiv.querySelectorAll('.field')
const formsetTotals = getFormsetCounters()


sortFields()
incrementFieldSelectorFormMaxOrder()


function deleteField(event) {
    // used in `./fieldForm.html` template
    // set delete marker and make div invisible
    event.preventDefault() // othervise page scrolls up for some reason
    const column = event.target.parentElement
    const deleteInput = column.querySelector('input[name$="DELETE"]')

    // if there is no deleteInput, it's not an initial (in DB) column,
    // we have to decrement FORMSET_TOTALS
    // and then we can just remove the column
    if (!deleteInput) {
        const typeName = column.querySelector('input').name.split('-')[0]
        formsetTotals[typeName]--
        column.remove()
        return
    }

    deleteInput.value = true
    column.hidden = true
}

function getFormsetCounters() {
    // initiate and return a table of form count per formset
    // later will be used in the management forms
    const formsetTotalInputs = document.querySelectorAll('input[name$=TOTAL_FORMS]')
    const formset_totals = Object.create(null)
    for (let formsetTotalInput of formsetTotalInputs) {
        let typeName = formsetTotalInput.name.replace('-TOTAL_FORMS', '')
        formset_totals[typeName] = Number(formsetTotalInput.value)
    }

    return formset_totals
}

function sortFields() {
    // sort field blocks by order
    const fields = Array(...getFields());
    fields
        .sort((a, b) => {
            let orderA = Number(a.querySelector('input[name$=order]').value)
            let orderB = Number(b.querySelector('input[name$=order]').value)
            return orderA - orderB
        })
        .forEach(field => {
            schemaFieldsDiv.appendChild(field)
        })
}

function normalizeFieldOrder() {
    // make all order fields to be consecutive starting from 1
    const fields = Array(...getFields())
    let order = 1
    for (let field of fields) {
        if (field.querySelector('input[name$="DELETE"]')?.value) {
            // skip field for removal
            continue
        }
        field.querySelector('input[name$=order]').value = order
        order++
    }
}

function getMaxOrder() {
    const orders = Array(
        ...schemaFieldsDiv.querySelectorAll('input[name$=order]')
    ).map(input => Number(input.value))

    return orders.length ? Math.max(...orders) : 0
}

function incrementFieldSelectorFormMaxOrder() {
    const orderInput = fieldSelectorForm.querySelector('input[name$=order]')
    orderInput.value = getMaxOrder() + 1
}


// Event listeners

document
    .getElementById('schemaForm')
    .addEventListener('submit', function (_target) {
        sortFields()
        normalizeFieldOrder()

        // update management forms' totals before submitting
        const formsetTotalInputs = schemaFieldsDiv.querySelectorAll('input[name$=TOTAL_FORMS]')
        for (let formsetTotalInput of formsetTotalInputs) {
            let typeName = formsetTotalInput.name.replace('-TOTAL_FORMS', '')
            formsetTotalInput.value = formsetTotals[typeName]
        }
    })

document
    .getElementById('addFieldBtn')
    .addEventListener('click', function (addBtn) {
        addBtn.preventDefault()

        if (!validateForm(fieldSelectorForm)) {
            // do not submit, let a user fix the input
            return
        }

        // set up new field form
        const { selectedType, fieldName, fieldOrder, formIndex } = getFormParams()
        const fieldForm = initForm(selectedType)
        setFormInputsIdsAndNames(fieldForm, formIndex)
        setFormNameAndOrder(fieldForm, fieldName, fieldOrder)

        // add the field to the form
        document.getElementById('schemaFields').appendChild(fieldForm)

        // reset the selector form
        fieldSelectorForm.reset()
        // and increment the selector's order input
        incrementFieldSelectorFormMaxOrder()
    })


function setFormNameAndOrder(fieldForm, fieldName, fieldOrder) {
    fieldForm.querySelector('input[name$="name"]').value = fieldName
    fieldForm.querySelector('input[name$="order"]').value = fieldOrder
}

function setFormInputsIdsAndNames(fieldForm, formIndex) {
    // set correct input ids assuming there are only inputs or selects 
    setInputsIdNameLabel('input', fieldForm, formIndex)
    setInputsIdNameLabel('select', fieldForm, formIndex)
}

function setInputsIdNameLabel(inputType, fieldForm, formIndex) {
    const inputs = fieldForm.querySelectorAll(inputType)
    for (let input of inputs) {
        let label = fieldForm.querySelector('label[for="' + input.id + '"]')
        input.id = input.id.replace('!', formIndex)
        input.name = input.name.replace('!', formIndex)
        label.setAttribute('for', input.id)
    }
}

function initForm(selectedType) {
    const fieldTemplates = document.getElementById('fieldTemplates')
    const fieldForm = fieldTemplates.querySelector('#' + selectedType).cloneNode(true)
    fieldForm.removeAttribute('id')
    fieldForm.style.display = ""
    return fieldForm
}

function validateForm(form) {
    if (!form.checkValidity()) {
        form.reportValidity()
        return false
    }
    return true
}

function getFormParams() {
    const fieldSelectorData = new FormData(fieldSelectorForm)
    const selectedType = fieldSelectorData.get('type')
    const fieldName = fieldSelectorData.get('name')
    const fieldOrder = fieldSelectorData.get('order')
    const formIndex = formsetTotals[selectedType]++
    return { selectedType, fieldName, fieldOrder, formIndex }
}
