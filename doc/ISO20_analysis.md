# What do we need for ISO15118-20?

- Chapter 7.3.1: TLS is mandatory. Exception: Connection setup.

- [V2G20-2348] private SECC shall contain a PE certificate, needed for TLS session.

- [V2G20-1238] In the SDP handshake, when the SECC intends to offer ISO 15118-20 communication, it shall respond to a TLS request by the EVCC with TLS.

- [V2G20-1237] If the established connection between EVCC and SECC is TLS 1.2 (or lower) or TCP without TLS the EVCC shall not offer ISO 15118-20 in SupportedAppProtocolReq.

- [V2G20-2356] If the established connection between EVCC and SECC is TLS 1.2 (or lower) or TCP without TLS the SECC shall not select ISO 15118-20  from SupportedAppProtocolReq.