#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject* compare(PyObject* self, PyObject* args) {
    Py_buffer snap1_buffer;
    Py_buffer snap2_buffer;
    if (!PyArg_ParseTuple(args, "y*y*", &snap1_buffer, &snap2_buffer)) {
        return NULL;
    }

    unsigned char* snap1 = snap1_buffer.buf;
    unsigned char* snap2 = snap2_buffer.buf;
    Py_ssize_t len = snap1_buffer.len;
    long count = 0;
    for (Py_ssize_t i = 0; i < len; i++) {
        if (snap1[i] && snap1[i] == snap2[i]) count++;
    }

    PyBuffer_Release(&snap1_buffer);
    PyBuffer_Release(&snap2_buffer);

    return PyLong_FromLong(count);
}

static PyObject* normalised_levenshtein(PyObject* self, PyObject* args) {
    Py_buffer snap1_buffer;
    Py_buffer snap2_buffer;
    if (!PyArg_ParseTuple(args, "y*y*", &snap1_buffer, &snap2_buffer)) {
        return NULL;
    }

    unsigned char* snap1 = snap1_buffer.buf;
    unsigned char* snap2 = snap2_buffer.buf;
    Py_ssize_t len = snap1_buffer.len;

    double similarity = -1.0;
    size_t row_size = sizeof(unsigned) * (len + 1);
    unsigned* prev_row = malloc(row_size);
    unsigned* curr_row = malloc(row_size);
    if (!prev_row || !curr_row) goto error;

    for (unsigned i = 0; i <= len; i++) {
        prev_row[i] = i;
    }
    for (unsigned i = 1; i <= len; i++) {
        for (unsigned n = 0; n <= len; n++) {
            curr_row[n] = i;
        }
        for (unsigned j = 1; j <= len; j++) {
            unsigned cost = (snap1[i - 1] == snap2[j - 1]) ? 0 : 1;
            unsigned a = curr_row[j - 1] + 1;    // Deletion
            unsigned b = prev_row[j] + 1;        // Insertion
            unsigned c = prev_row[j - 1] + cost; // Substitution
            curr_row[j] = (a < b) ? ((a < c) ? a : c) : ((b < c) ? b : c);
        }
        memcpy(prev_row, curr_row, row_size);
    }
    double distance = prev_row[len];
    similarity = 1.0 - distance / len;

error:
    if (prev_row) free(prev_row);
    if (curr_row) free(curr_row);
    PyBuffer_Release(&snap1_buffer);
    PyBuffer_Release(&snap2_buffer);

    return PyFloat_FromDouble(similarity);
}

static PyMethodDef LibZ80DiffMethods[] = {
    {"compare", compare, METH_VARARGS, "Return a count of equal bytes in two snapshots."},
    {"normalised_levenshtein", normalised_levenshtein, METH_VARARGS, "Return the Normalised Levenshtein Distance between two snapshots."},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

static struct PyModuleDef libz80diffmodule = {
    PyModuleDef_HEAD_INIT,
    "libz80diff",     /* name of module */
    NULL,             /* module documentation, may be NULL */
    -1,               /* size of per-interpreter state of the module,
                         or -1 if the module keeps state in global variables. */
    LibZ80DiffMethods
};

PyMODINIT_FUNC PyInit_libz80diff(void) {
    return PyModule_Create(&libz80diffmodule);
}
