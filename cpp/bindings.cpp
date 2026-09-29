#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "chaos.hpp"

namespace py = pybind11;

std::string ping() {
    return "chaoshash module loaded OK";
}

py::bytes py_transform(
    py::array_t<int32_t, py::array::c_style | py::array::forcecast> x_q,
    uint64_t state,
    uint64_t r_param,
    int m
) {
    py::buffer_info buf = x_q.request();
    if (buf.ndim != 1) {
        throw std::invalid_argument("Input quantized vector x_q must be 1-dimensional");
    }

    const int32_t* ptr = static_cast<const int32_t*>(buf.ptr);
    size_t d = buf.shape[0];

    std::vector<uint8_t> packed = zkcambio::transform_core(ptr, d, state, r_param, m);
    return py::bytes(reinterpret_cast<const char*>(packed.data()), packed.size());
}

double py_hamming(
    py::bytes a,
    py::bytes b,
    int m = -1
) {
    std::string s_a = a;
    std::string s_b = b;

    return zkcambio::hamming_distance(
        reinterpret_cast<const uint8_t*>(s_a.data()), s_a.size(),
        reinterpret_cast<const uint8_t*>(s_b.data()), s_b.size(),
        m
    );
}

bool py_has_cycle_within(
    uint64_t state,
    uint64_t r_param,
    uint64_t max_steps
) {
    return zkcambio::has_cycle_within(state, r_param, max_steps);
}

py::bytes py_stream_matrix_bits(
    uint64_t state,
    uint64_t r_param,
    size_t n_bits
) {
    std::vector<uint8_t> bits = zkcambio::stream_matrix_bits(state, r_param, n_bits);
    return py::bytes(reinterpret_cast<const char*>(bits.data()), bits.size());
}

PYBIND11_MODULE(chaoshash, m) {
    m.doc() = "ZK-CaMBio C++ Fixed-Point Chaos Engine (chaoshash)";

    m.def("ping", &ping, "Returns chaoshash module status string");

    m.def("transform", &py_transform,
          py::arg("x_q"),
          py::arg("state"),
          py::arg("r_param"),
          py::arg("m") = 512,
          "Transforms quantized biometric vector x_q into m-bit chaotic cancelable template");

    m.def("hamming", &py_hamming,
          py::arg("a"),
          py::arg("b"),
          py::arg("m") = -1,
          "Computes normalized Hamming distance between two packed bit strings");

    m.def("has_cycle_within", &py_has_cycle_within,
          py::arg("state"),
          py::arg("r_param"),
          py::arg("max_steps") = 2000000ULL,
          "Detects if chaotic map enters a cycle within max_steps using Brent's algorithm");

    m.def("stream_matrix_bits", &py_stream_matrix_bits,
          py::arg("state"),
          py::arg("r_param"),
          py::arg("n_bits"),
          "Generates raw packed matrix bits from chaotic generator for statistical tests");
}

