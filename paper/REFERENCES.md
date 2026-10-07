# Reference candidates for the ZK-CaMBio paper

**Legend**
- ✅ = I found the paper's listing (publisher, arXiv, DBLP or institutional page) with a web search this session and the details match. I did not read the full text, so read the paper before citing any claim from it.
- ⚠️ = from memory, not checked this session. Confirm authors, year, venue and pages on the publisher page before using.
- Rule for the paper: cite only what you have opened. If you cannot confirm an entry, leave it out.

## 1. Cancelable biometrics: foundations and reviews
- ✅ Ratha, Connell, Bolle. *Enhancing security and privacy in biometrics-based authentication systems.* IBM Systems Journal 40(3):614-634, 2001. (origin of the term "cancelable biometrics")
- ✅ Ratha, Chikkerur, Connell, Bolle. *Generating cancelable fingerprint templates.* IEEE TPAMI 29(4):561-572, 2007.
- ✅ Nandakumar, Jain. *Biometric template protection: Bridging the performance gap between theory and practice.* IEEE Signal Processing Magazine, 2015 (DOI 10.1109/MSP.2015.2427849). Key point for you: protection schemes seldom deliver non-invertibility, revocability and unlinkability without hurting accuracy.
- ✅ (existence; check exact title) Patel, Ratha, Chellappa. Review of cancelable biometrics, IEEE Signal Processing Magazine, September 2015.
- ⚠️ Rathgeb, Uhl. *A survey on biometric cryptosystems and cancelable biometrics.* EURASIP J. Information Security, 2011.
- ⚠️ Jain, Nandakumar, Nagar. *Biometric template security.* EURASIP J. Advances in Signal Processing, 2008.
- ⚠️ Jain, Ross, Nandakumar. *Introduction to Biometrics.* Springer, 2011. (textbook)
- You own: Maltoni, Maio, Jain, Feng. *Handbook of Fingerprint Recognition*, 3rd ed., Springer 2021 (FVC databases, sensor details).

## 2. BioHashing / random projection and its analysis
- ✅ Teoh, Ngo, Goh. *BioHashing: two factor authentication featuring fingerprint data and tokenised random number.* Pattern Recognition 37(11):2245-2255, 2004.
- ✅ Kong et al. *An analysis of BioHashing and its variants.* Pattern Recognition, 2006 (DOI 10.1016/j.patcog.2005.10.025). Argues the zero-EER claim rests on a hidden assumption (a genuine, unique token). Verify the author list.
- ✅ Lumini, Nanni. *An improved BioHashing for human authentication.* Pattern Recognition 40:1057-1065, 2007. (stolen-token problem)
- ✅ Teoh, Kuan, Lee. *Cancellable biometrics and annotations on BioHash.* Pattern Recognition 41(6):2034-2044, 2008. (stolen-biometric vs stolen-token scenarios)
- ✅ Nanni, Lumini. *Empirical tests on BioHashing.* Neurocomputing 69:2390-2395, 2006. (includes face + fingerprint BioHashing fusion)
- ⚠️ Charikar. *Similarity estimation techniques from rounding algorithms.* STOC 2002. (hyperplane hashing, Pr = theta/pi)
- ⚠️ Goemans, Williamson. *Improved approximation algorithms for maximum cut and satisfiability problems using semidefinite programming.* JACM 1995. (the arccos/pi identity)
- ⚠️ Indyk, Motwani. *Approximate nearest neighbors: towards removing the curse of dimensionality.* STOC 1998.
- ⚠️ Johnson, Lindenstrauss. *Extensions of Lipschitz mappings into a Hilbert space.* 1984.

## 3. Attacks on templates: inversion, pre-image, hill-climbing
- ✅ Gomez-Barrero, Galbally. *Reversing the irreversible: A survey on inverse biometrics.* Computers & Security 90, 101700, 2020.
- ✅ Mai, Cao, Yuen, Jain. *On the reconstruction of face images from deep face templates.* IEEE TPAMI (DOI 10.1109/TPAMI.2018.2827389). Shows deep face templates can be inverted.
- ✅ Lacharme, Cherrier, Rosenberger. *Preimage attack on BioHashing.* SECRYPT 2013. (genetic algorithm, given seed and BioCode)
- ✅ (arXiv 1905.03021, verify authors/venue) *A genetic algorithm enabled similarity-based attack on cancellable biometrics.* Reports that longer BioHash codes give better accuracy but weaker resistance. Directly relevant to your m trade-off.
- ✅ (arXiv 1910.07770, verify authors/venue) *On the risk of cancelable biometrics.* Pre-image attack on BioHashing; same finding about code length.
- ✅ Adler. *Vulnerabilities in biometric encryption systems.* AVBPA 2005 (hill-climbing on match scores).
- ✅ Galbally, McCool, Fierrez, Marcel, Ortega-Garcia. *On the vulnerability of face verification systems to hill-climbing attacks.* Pattern Recognition (2009/2010; verify volume).
- ⚠️ Uludag, Jain. *Attacks on biometric systems: a case study in fingerprints.* SPIE 2004.
- ⚠️ Cappelli, Lumini, Maio, Maltoni. *Fingerprint image reconstruction from standard templates.* TPAMI 2007.

## 4. Evaluation frameworks and standards
- ✅ ISO/IEC 30136:2018, *Performance testing of biometric template protection schemes.* (accuracy, attack probability, information leakage, diversity/unlinkability). Under revision.
- ⚠️ ISO/IEC 24745, *Biometric information protection* (irreversibility, unlinkability, renewability; check the edition year).
- ✅ Gomez-Barrero, Galbally, Rathgeb, Busch. *General framework to evaluate unlinkability in biometric template protection systems.* IEEE TIFS 13:1406-1420, 2018 (DOI 10.1109/TIFS.2017.2788000). Source of D_sys. Reference implementation: github.com/dasec/unlinkability-metric (academic use; the authors ask that you cite the TIFS paper).
- ⚠️ ISO/IEC 19795-1 (biometric performance testing).
- ⚠️ Efron, Tibshirani. *An Introduction to the Bootstrap.* 1993; Bolle, Ratha, Pankanti. *Error analysis of pattern recognition systems: the subsets bootstrap.* CVIU 2004.

## 5. Multimodal fusion and multibiometric template protection
- ✅ Nagar, Nandakumar, Jain. *Multibiometric cryptosystems based on feature-level fusion.* IEEE TIFS 7(1):255-268, 2012. Uses a real and a virtual multimodal database (a precedent for your chimeric protocol).
- ⚠️ Ross, Jain. *Information fusion in biometrics.* Pattern Recognition Letters 24(13), 2003 (verify year; your draft says 2004).
- ⚠️ Gomez-Barrero, Rathgeb, Li, Ramachandra, Galbally, Busch. *Multi-biometric template protection based on Bloom filters.* Information Fusion, 2018. ⚠️ And the Bloom-filter unlinkability paper your draft cites (Information Sciences): confirm year (I believe 2016, not 2017) and exact title.

## 6. Chimeric (virtual) multimodal databases: validity
- ✅ Poh, Bengio. *Can chimeric persons be used in multimodal biometric authentication experiments?* MLMI 2005, LNCS 3869, pp. 87-100. **Important:** they report the practice is "questionable" for a large share of experiments. Cite it, and add your multi-seed pairing sensitivity experiment.
- ✅ Nagar et al. 2012 (above) used a virtual multimodal database.

## 7. Datasets and encoders
- ✅ Bansal, Nanduri, Castillo, Ranjan, Chellappa. *UMDFaces: An annotated face dataset for training deep networks.* arXiv 1611.01484 (367,888 images, 8,277 subjects). Check the venue (I believe IJCB 2017).
- ✅ Cao, Shen, Xie, Parkhi, Zisserman. *VGGFace2: A dataset for recognising faces across pose and age.* IEEE FG 2018. (3.31M images, 9,131 subjects)
- ✅ Maio, Maltoni, Cappelli, Wayman, Jain. *FVC2004: Third Fingerprint Verification Competition.* ICBA 2004, LNCS 3072.
- ⚠️ Schroff, Kalenichenko, Philbin. *FaceNet.* CVPR 2015. ⚠️ Szegedy, Ioffe, Vanhoucke, Alemi. *Inception-v4, Inception-ResNet and the impact of residual connections on learning.* AAAI 2017 (defines the Inception-ResNet family). ⚠️ the facenet-pytorch repository (T. Esler) for the exact pretrained weights you used (cite it as software).
- ⚠️ He, Zhang, Ren, Sun. *Deep residual learning for image recognition.* CVPR 2016. ⚠️ Wang et al. *CosFace.* CVPR 2018. ⚠️ Deng et al. *ArcFace.* CVPR 2019.

## 8. Zero-knowledge and biometrics (for the "zero-knowledge" definition paragraph)
- ✅ (arXiv 2310.19452; verify authors/venue) *Incorporating zero-knowledge succinct non-interactive argument of knowledge for blockchain-based identity management with off-chain computations.* Cancelable fingerprint templates + zk-SNARK on FVC2002/2004/2006.
- ✅ (PMC12173353; verify authors/venue, 2025) A ZKP-based anonymous biometric authentication scheme for e-health systems (multimodal cancelable biometrics + Pedersen commitments).
- ✅ Keuffer. *Verifiable computation and biometric authentication.* PhD thesis, EURECOM. Related: ✅ "A Biometric Self Authentication Scheme" (SciTePress, 2023).
- Use these to say precisely what a real ZK-biometric system does, and that yours does not.

## 9. Fuzzy commitment / vault / extractors, and key derivation
- ⚠️ Juels, Wattenberg. *A fuzzy commitment scheme.* ACM CCS 1999. ⚠️ Juels, Sudan. *A fuzzy vault scheme.* 2006. ⚠️ Dodis, Ostrovsky, Reyzin, Smith. *Fuzzy extractors.* SIAM J. Computing 2008.
- ⚠️ Percival. *Stronger key derivation via sequential memory-hard functions* (scrypt), 2009; RFC 7914. ⚠️ Krawczyk, Bellare, Canetti. *HMAC*, RFC 2104.
- ⚠️ May. *Simple mathematical models with very complicated dynamics.* Nature 1976 (logistic map). ⚠️ Alvarez, Li. *Some basic cryptographic requirements for chaos-based cryptosystems.* Int. J. Bifurcation and Chaos 2006 (for your limitation about chaotic generators).

## Suggested comparison table for Related Work
Rows: BioHashing (Teoh 2004), Cancelable fingerprint transforms (Ratha 2007), Multibiometric fuzzy vault/commitment (Nagar 2012), Bloom-filter protection (Gomez-Barrero et al.), ZK-based schemes (Kothari 2023 etc.), ZK-CaMBio. Columns: modalities, protection type, evaluated attacks, unlinkability analysis, what is claimed on irreversibility. Fill from the papers themselves after reading them.
