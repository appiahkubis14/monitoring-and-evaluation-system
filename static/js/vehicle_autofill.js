document.addEventListener("DOMContentLoaded", function () {
    const vehicleTypeField = document.getElementById("id_vehicle_type");
    const makeField = document.getElementById("id_make");
    const modelField = document.getElementById("id_model");

    function updateVehicleFields() {
        const selectedOption = vehicleTypeField.options[vehicleTypeField.selectedIndex];
        if (selectedOption && selectedOption.text.includes("-")) {
            const [type, makeModel] = selectedOption.text.split(" - ");
            const [make, model] = makeModel.split(" ");
            makeField.value = make || "";
            modelField.value = model || "";
        }
    }

    if (vehicleTypeField) {
        vehicleTypeField.addEventListener("change", updateVehicleFields);
    }
});
