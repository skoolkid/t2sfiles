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

static PyMethodDef LibZ80DiffMethods[] = {
    {"compare", compare, METH_VARARGS, "Return a count of equal bytes in two snapshots."},
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
